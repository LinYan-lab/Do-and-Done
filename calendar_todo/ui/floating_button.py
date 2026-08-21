"""角落悬浮按钮：无边框、始终置顶、可拖动，点击触发 clicked 信号。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class FloatingButton(QWidget):
    # 点击（不是拖动）时发出这个信号，供外部（app.py）响应
    clicked = Signal()

    def __init__(self):
        super().__init__(None)

        # FramelessWindowHint：去掉系统标题栏
        # WindowStaysOnTopHint：始终置顶
        # Tool：不出现在任务栏，像一个“小工具”
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setFixedSize(48, 48)

        # 记录鼠标按下时的位置，用于区分“点击”和“拖动”
        self._press_global = None
        self._drag_offset = None

    # ---------- 外观 ----------

    def paintEvent(self, event):
        """每次需要重绘时被调用：画一个圆角蓝色方块，中间写“日”。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor("#2D6CDF"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)

        painter.setPen(QColor("white"))
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(18)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "日")

    # ---------- 鼠标交互：拖动 vs 点击 ----------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_global = event.globalPosition().toPoint()
            self._drag_offset = self._press_global - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self._press_global is not None:
            # manhattanLength：横向+纵向移动距离之和；小于 5 像素视为“点击”
            moved = (event.globalPosition().toPoint() - self._press_global).manhattanLength()
            if moved < 5:
                self.clicked.emit()
        self._press_global = None
        self._drag_offset = None
        event.accept()
