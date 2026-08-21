"""日历日期小格子：显示一个日期的数字，支持今天高亮和选中态。

月历视图和滚动日历条都复用这个格子，以后颜色同步也在这里做。
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

        self.setMinimumSize(40, 40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.number_label = QLabel(str(day.day))
        self.number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.number_label)

        self._apply_style()

    def set_selected(self, selected: bool):
        """切换选中态（点击日期时由视图调用）。"""
        self._selected = selected
        self._apply_style()

    def _apply_style(self):
        """根据“今天/选中/当月/其他月”四种状态决定长相。"""
        if self._is_today:
            style = (
                "background:#2D6CDF; border:none; border-radius:8px;"
                "color:white; font-weight:bold; font-size:14px;"
            )
        elif self._selected:
            style = (
                "background:#E8F0FE; border:2px solid #2D6CDF; border-radius:8px;"
                "color:#1F2937; font-size:14px;"
            )
        elif self._in_current_month:
            style = (
                "background:#F8F9FA; border:1px solid #E6E9EF; border-radius:8px;"
                "color:#1F2937; font-size:14px;"
            )
        else:
            style = (
                "background:transparent; border:none; border-radius:8px;"
                "color:#B7BDC7; font-size:14px;"
            )
        self.setStyleSheet(style)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.day)
            event.accept()
