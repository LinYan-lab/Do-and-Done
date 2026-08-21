"""日历面板：从悬浮按钮展开，可在“滚动日历”和“完整月历”两种形态间切换。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from calendar_todo.ui.month_view import MonthView
from calendar_todo.ui.strip_view import StripView


class _TitleBar(QFrame):
    """标题栏：显示标题和按钮，按住它可以直接拖动整个面板。"""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(38)
        self.setStyleSheet(
            "background:#2D6CDF;"
            "border-top-left-radius:10px;"
            "border-top-right-radius:10px;"
        )
        self._drag_offset = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        event.accept()


class CalendarPanel(QWidget):
    """无边框置顶面板，内容是一个可切换两种形态的堆叠视图。"""

    MODE_STRIP = "strip"    # 滚动日历（一小段时间）
    MODE_MONTH = "month"    # 完整月历（一个月）

    date_selected = Signal(object)  # 用户在任一视图里选中某天时转发出去

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setFixedWidth(380)
        self.setStyleSheet(
            "background:white; border:1px solid #d0d5dd; border-radius:10px;"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- 顶部标题栏 ----
        self.title_bar = _TitleBar()
        bar_layout = QHBoxLayout(self.title_bar)
        bar_layout.setContentsMargins(12, 0, 8, 0)
        bar_layout.setSpacing(8)

        title = QLabel("日历 ToDo")
        title.setStyleSheet("color:white; font-weight:bold; font-size:14px;")

        self.toggle_button = QPushButton("展开月历")
        self.toggle_button.setStyleSheet(
            "QPushButton{background:#3D7BFF; color:white; border:none;"
            " border-radius:5px; padding:4px 10px;}"
            "QPushButton:hover{background:#4D88FF;}"
        )
        self.close_button = QPushButton("✕")
        self.close_button.setStyleSheet(
            "QPushButton{background:transparent; color:white; border:none;"
            " font-size:16px; padding:2px 8px;}"
            "QPushButton:hover{background:#C0392B; border-radius:5px;}"
        )

        bar_layout.addWidget(title)
        bar_layout.addStretch(1)
        bar_layout.addWidget(self.toggle_button)
        bar_layout.addWidget(self.close_button)

        # ---- 内容区：滚动日历条 + 完整月历 ----
        self.stack = QStackedWidget()
        self.strip_view = StripView()
        self.month_view = MonthView()
        self.stack.addWidget(self.strip_view)
        self.stack.addWidget(self.month_view)

        root.addWidget(self.title_bar)
        root.addWidget(self.stack)

        # ---- 信号连接 ----
        self.toggle_button.clicked.connect(self.toggle_mode)
        self.close_button.clicked.connect(self.hide)
        self.strip_view.date_selected.connect(self.date_selected)
        self.month_view.date_selected.connect(self.date_selected)

        self._mode = self.MODE_STRIP
        self._apply_mode()

    @property
    def current_mode(self) -> str:
        """当前形态：MODE_STRIP 或 MODE_MONTH。"""
        return self._mode

    def show_strip(self):
        """以“滚动日历”形态显示面板。"""
        self._mode = self.MODE_STRIP
        self._apply_mode()
        self.show()

    def toggle_mode(self):
        """在滚动日历和完整月历之间切换。"""
        self._mode = self.MODE_MONTH if self._mode == self.MODE_STRIP else self.MODE_STRIP
        self._apply_mode()

    def _apply_mode(self):
        """根据当前形态切换显示页和面板高度。"""
        if self._mode == self.MODE_MONTH:
            self.stack.setCurrentIndex(1)
            self.setFixedHeight(430)
            self.toggle_button.setText("收起为滚动")
        else:
            self.stack.setCurrentIndex(0)
            self.setFixedHeight(180)
            self.toggle_button.setText("展开月历")
