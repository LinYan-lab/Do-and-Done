"""日历面板：从悬浮按钮展开，可在“滚动日历”和“完整月历”两种形态间切换。

阶段 1：两种形态都只是占位提示，真正的日历内容在阶段 2 实现。
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


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

        # ---- 内容区：两个占位页 ----
        self.stack = QStackedWidget()
        self.stack.addWidget(self._make_placeholder("滚动日历\n（阶段 2：展示一段时间的日期）"))
        self.stack.addWidget(self._make_placeholder("完整月历\n（阶段 2：展示一个月所有日期）"))

        root.addWidget(self.title_bar)
        root.addWidget(self.stack)

        # ---- 信号连接 ----
        self.toggle_button.clicked.connect(self.toggle_mode)
        self.close_button.clicked.connect(self.hide)

        self._mode = self.MODE_STRIP
        self._apply_mode()

    @staticmethod
    def _make_placeholder(text: str) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color:#666666; background:white; font-size:14px;")
        return label

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
            self.setFixedHeight(420)
            self.toggle_button.setText("收起为滚动")
        else:
            self.stack.setCurrentIndex(0)
            self.setFixedHeight(150)
            self.toggle_button.setText("展开月历")
