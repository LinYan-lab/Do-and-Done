"""角落悬浮按钮：一张手绘感的小便签，轻微旋转，悬停抬起、按下压回。"""

from PySide6.QtCore import QPoint, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from calendar_todo.ui import theme


class FloatingButton(QWidget):
    clicked = Signal()

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

        self.setFixedSize(52, 52)

        self._hover = False
        self._pressed = False
        self._press_pos = None
        self._drag_offset = None

    # ---------- 外观 ----------

    def paintEvent(self, event):
        """画一张淡黄便签：硬阴影 + 纸面 + 抖动边框 + 手写“日”。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 画布中心旋转：悬停时微微转正，平时歪一点，按下再歪一点
        painter.save()
        painter.translate(self.width() / 2, self.height() / 2)
        if self._pressed:
            painter.rotate(2.5)
        elif self._hover:
            painter.rotate(-1.0)
        else:
            painter.rotate(-2.0)
        painter.translate(-self.width() / 2, -self.height() / 2)

        rect = QRectF(self.rect()).adjusted(2, 2, -5, -5)
        if self._pressed:
            theme.draw_hard_shadow(painter, rect, QPoint(1, 1), theme.SHADOW, 8)
        elif self._hover:
            theme.draw_hard_shadow(painter, rect, QPoint(4, 5), theme.SHADOW, 8)
        else:
            theme.draw_hard_shadow(painter, rect, QPoint(3, 3), theme.SHADOW, 8)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(
            QColor(theme.STICKY_YELLOW if not self._pressed else "#F5E3A8")
        )
        painter.drawRoundedRect(rect, 8, 8)
        theme.draw_sketch_rect(painter, rect, theme.INK, wobble=1.3, pen_width=1.6)

        painter.setPen(QColor(theme.INK))
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(19)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "日")
        painter.restore()

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    # ---------- 鼠标交互：拖动 vs 点击 ----------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.globalPosition().toPoint()
            self._drag_offset = self._press_pos - self.frameGeometry().topLeft()
            self._pressed = True
            self.update()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self._press_pos is not None:
            moved = (event.globalPosition().toPoint() - self._press_pos).manhattanLength()
            if moved < 5:
                self.clicked.emit()
        self._press_pos = None
        self._drag_offset = None
        self._pressed = False
        self.update()
        event.accept()
