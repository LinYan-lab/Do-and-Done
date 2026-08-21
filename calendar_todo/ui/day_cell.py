"""日历日期小格子：显示日期数字、今天标记、选中态，以及按完成率染色的背景。

月历视图和滚动日历条都复用这个格子，颜色逻辑只在这里实现一次。
"""

from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout


class DayCell(QFrame):
    clicked = Signal(object)  # 点击时把这一天发出去

    def __init__(self, day: date, is_today: bool = False, in_current_month: bool = True):
        super().__init__()
        self.day = day
        self._is_today = is_today
        self._in_current_month = in_current_month
        self._selected = False
        self._completion_color = None  # 完成率颜色，None 表示不染色

        self.setMinimumSize(40, 40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        self.number_label = QLabel(str(day.day))
        self.number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.number_label, 1)

        # 节日/纪念日名称的小字（默认隐藏）
        self.sub_label = QLabel("")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setFixedHeight(11)
        layout.addWidget(self.sub_label)

        # “今天”小圆点标记：放在格子底部，颜色再花哨也能认出今天
        self.today_badge = QLabel("●")
        self.today_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.today_badge.setStyleSheet(
            "color:#111827; background:transparent; font-size:9px;"
        )
        self.today_badge.setFixedHeight(10)
        layout.addWidget(self.today_badge)

        self._apply_style()

    def set_selected(self, selected: bool):
        """切换选中态（点击日期时由视图调用）。"""
        self._selected = selected
        self._apply_style()

    def set_completion_color(self, color):
        """设置完成率颜色（来自逻辑层）；None 表示不染色。"""
        self._completion_color = color
        self._apply_style()

    def set_sub_text(self, text: str):
        """设置格子下方的小字（节日/纪念日名称）；空字符串表示隐藏。"""
        if len(text) > 6:
            text = text[:5] + "…"
        self.sub_label.setText(text)
        self.sub_label.setVisible(bool(text))

    def _apply_style(self):
        """根据“完成率颜色/今天/选中/当月”决定格子的长相。"""
        # 背景：优先用完成率颜色，其次今天的蓝，再其次默认浅灰
        if self._completion_color is not None:
            background = self._completion_color
        elif self._is_today:
            background = "#2D6CDF"
        elif self._in_current_month:
            background = "#F8F9FA"
        else:
            background = "transparent"

        # 文字颜色：彩色背景上白字，浅色背景上深字
        if self._completion_color is not None or self._is_today:
            text_color = "white"
        elif self._in_current_month:
            text_color = "#1F2937"
        else:
            text_color = "#B7BDC7"

        # 边框：选中只保留最外层的细黑圈，不再叠加其他边框
        if self._selected:
            border = "1px solid #111827"
        elif (
            self._completion_color is None
            and not self._is_today
            and self._in_current_month
        ):
            border = "1px solid #E6E9EF"
        else:
            border = "none"

        weight = "bold" if self._is_today else "normal"
        self.setStyleSheet(
            f"background:{background}; border:{border}; border-radius:8px;"
            f" color:{text_color}; font-size:14px; font-weight:{weight};"
        )
        self.sub_label.setStyleSheet(
            f"color:{text_color}; background:transparent; font-size:8px;"
        )
        self.today_badge.setVisible(self._is_today)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.day)
            event.accept()
