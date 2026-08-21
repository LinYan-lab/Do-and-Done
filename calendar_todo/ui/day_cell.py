"""日历日期小格子：手绘纸片效果，支持今天标记、选中态、完成率底色。

月历和滚动条共用；背景/边框/阴影全部由 paintEvent 自绘，
数字和节日小字是透明的子标签。
"""

from datetime import date

from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout

from calendar_todo.logic import completion
from calendar_todo.ui import theme


class DayCell(QFrame):
    clicked = Signal(object)

    def __init__(self, day: date, is_today: bool = False, in_current_month: bool = True):
        super().__init__()
        self.day = day
        self._is_today = is_today
        self._in_current_month = in_current_month
        self._selected = False
        self._hover = False
        self._completion_color = None  # 完成率颜色，None 表示不染色

        self.setAttribute(Qt.WidgetAttribute.WA_Hover)  # 开启悬停状态跟踪
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(40, 40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 3, 4, 2)
        layout.setSpacing(0)

        self.number_label = QLabel(str(day.day))
        self.number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.number_label.setStyleSheet("background:transparent;")
        layout.addWidget(self.number_label, 1)

        # 节日/纪念日小字（默认隐藏）
        self.sub_label = QLabel("")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet("background:transparent;")
        self.sub_label.setFixedHeight(11)
        layout.addWidget(self.sub_label)

        # “今天”小标记：手写体的“今”
        self.today_badge = QLabel("今")
        self.today_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.today_badge.setStyleSheet("background:transparent;")
        self.today_badge.setFixedHeight(10)
        layout.addWidget(self.today_badge)

        self._apply_style()

    # ---------- 状态 ----------

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style()

    def set_completion_color(self, color):
        self._completion_color = color
        self._apply_style()

    def set_sub_text(self, text: str):
        if len(text) > 6:
            text = text[:5] + "…"
        self.sub_label.setText(text)
        self.sub_label.setVisible(bool(text))

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    # ---------- 外观 ----------

    def _apply_style(self):
        """根据状态决定纸面颜色和文字颜色，然后重绘。"""
        if self._completion_color is not None:
            background = self._completion_color
        elif self._is_today:
            background = theme.STICKY_BLUE
        elif self._in_current_month:
            background = theme.PAPER
        else:
            background = None  # 透明：前后月的补位天

        if self._completion_color is not None:
            text_color = completion.text_color_for(self._completion_color)
        elif self._is_today:
            text_color = theme.INK  # 浅蓝便签底用深墨字
        elif self._in_current_month:
            text_color = theme.INK
        else:
            text_color = theme.INK_SOFT

        size = 14 if not self._is_today else 15
        self.number_label.setStyleSheet(
            f"background:transparent; color:{text_color};"
            f" font-size:{size}px; font-weight:bold;"
        )
        self.sub_label.setStyleSheet(
            f"background:transparent; color:{text_color}; font-size:8px;"
        )
        self.today_badge.setStyleSheet(
            f"background:transparent; color:{theme.INK}; font-size:9px; font-weight:bold;"
        )
        self.today_badge.setVisible(self._is_today)
        self.update()

    def paintEvent(self, event):
        """手绘纸片：硬阴影 + 纸面 + 抖动边框。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(1, 1, -4, -4)

        if self._completion_color is not None:
            background = QColor(self._completion_color)
        elif self._is_today:
            background = QColor(theme.STICKY_BLUE)
        elif self._in_current_month:
            background = QColor(theme.PAPER)
        else:
            background = None

        if background is None:
            return  # 前后月的补位天：什么都不画，只留浅色文字

        # 悬停时纸片“抬起来”：阴影更深、更远
        if self._hover and not self._selected:
            theme.draw_hard_shadow(painter, rect, QPoint(3, 4), theme.SHADOW, 6)
        else:
            theme.draw_hard_shadow(painter, rect, QPoint(2, 2), theme.SHADOW, 6)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(rect, 6, 6)

        # 选中：加粗墨线边框；普通纸片：铅笔细线
        if self._selected:
            theme.draw_sketch_rect(painter, rect, theme.INK, wobble=1.0, pen_width=2.2)
        elif self._in_current_month:
            theme.draw_sketch_rect(painter, rect, theme.PENCIL, wobble=1.0, pen_width=1.1)
