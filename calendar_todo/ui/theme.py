"""全局主题：手绘涂鸦（Hand-Drawn Sketch）风格。

像一张被认真整理过的笔记本：点阵纸背景、粉彩便签卡片、
略抖动的铅笔线条、硬边投影、手写字体；悬停抬起、按下收回。
"""

import random

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsDropShadowEffect

# ---------- 纸张与墨水 ----------
PAPER = "#FBF9F2"       # 纸白
PAPER_DARK = "#F4F1E6"  # 略旧的纸
GRID = "#E5E1D4"        # 点阵
INK = "#3B4252"         # 深蓝灰手写墨色
INK_SOFT = "#6B7488"    # 注释灰蓝
PENCIL = "#8A93A6"      # 铅笔灰

# ---------- 便签粉彩 ----------
STICKY_YELLOW = "#FFF3C4"
STICKY_PINK = "#FDE2E4"
STICKY_BLUE = "#DCEEFB"
STICKY_GREEN = "#DFF2D8"

# 硬边阴影（像纸张在桌面上投下的形状）
SHADOW = "#C9C3B4"

# 手写字体：楷体优先，其次漫画体，最后无衬线兜底
FONT_HAND = "AR PL UKai CN"

# ---------- 公共样式 ----------
TITLE_BAR = (
    f"background:{PAPER}; border:none;"
    "border-bottom:2px dashed #8A93A6;"
)

TITLE_TEXT = f"color:{INK}; font-weight:bold; font-size:15px;"

PRIMARY_BUTTON = (
    f"QPushButton{{background:{STICKY_YELLOW}; border:2px solid {INK};"
    f" border-radius:6px; color:#3B4252; font-size:13px; padding:4px 10px;}}"
    f"QPushButton:hover{{background:#FFF6D6; border-width:3px;}}"
    f"QPushButton:pressed{{padding-top:6px;}}"
)

NAV_BUTTON = (
    f"QPushButton{{background:{PAPER}; border:2px solid {PENCIL};"
    f" border-radius:6px; color:#3B4252; font-size:13px;}}"
    f"QPushButton:hover{{background:#FFFDF7; border-color:{INK};}}"
    f"QPushButton:pressed{{padding-top:2px;}}"
)

LIGHT_BUTTON = NAV_BUTTON

GHOST_BUTTON = (
    f"QPushButton{{background:{PAPER}; border:2px solid {INK};"
    f" border-radius:6px; color:#3B4252; font-size:12px; padding:3px 8px;}}"
    f"QPushButton:hover{{background:#FFFDF7;}}"
    f"QPushButton:pressed{{padding-top:5px;}}"
)

DANGER_ICON = (
    "QPushButton{background:transparent; color:#9A9387; border:none; font-size:13px;}"
    "QPushButton:hover{background:#F6D0C4; color:#B85C4A; border-radius:5px;}"
)

INPUT_FIELD = (
    "QLineEdit, QSpinBox, QDateEdit{background:#FFFDF7; border:2px solid #8A93A6;"
    " border-radius:5px; padding:4px 6px; color:#3B4252;}"
    "QLineEdit:focus, QSpinBox:focus, QDateEdit:focus{"
    " border-width:3px; border-color:#3B4252;}"
)

DIALOG_BUTTONS = (
    f"QDialogButtonBox QPushButton{{background:{STICKY_YELLOW};"
    f" border:2px solid #3B4252; border-radius:6px; color:#3B4252;"
    f" padding:4px 14px;}}"
    f"QDialogButtonBox QPushButton:hover{{background:#FFF6D6; border-width:3px;}}"
)


def make_panel_background(width: int, height: int) -> QPixmap:
    """点阵纸背景 + 几处铅笔 doodle（螺旋、波浪、小箭头）。"""
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.fillRect(pixmap.rect(), QColor(PAPER))

    # 点阵：间距 18px 的淡灰小圆点，带一点点随机偏移，像笔记本纸
    rng = random.Random(7)
    pen = QPen(QColor(GRID), 1)
    painter.setPen(pen)
    for x in range(8, width, 18):
        for y in range(8, height, 18):
            jx = rng.randint(-1, 1)
            jy = rng.randint(-1, 1)
            painter.drawPoint(x + jx, y + jy)

    _paint_doodles(painter, width, height)
    painter.end()
    return pixmap


def _paint_doodles(painter: QPainter, width: int, height: int):
    """右上角几笔低透明度的铅笔涂鸦，营造手帐氛围。"""
    color = QColor(PENCIL)
    color.setAlpha(110)
    pen = QPen(color, 1.2)
    painter.setPen(pen)

    # 螺旋（右上角）
    cx, cy = width - 64, 34
    radius = 4
    path = QPainterPath(QPointF(cx + radius, cy))
    for angle in range(0, 560, 40):
        r = radius + angle * 0.018
        rad = angle * 3.14159 / 180
        path.lineTo(QPointF(cx + r * _cos(rad), cy + r * _sin(rad)))
    painter.drawPath(path)

    # 波浪线（螺旋下方）
    start_x = width - 96
    y = 52
    path = QPainterPath(QPointF(start_x, y))
    for i in range(1, 5):
        x = start_x + i * 10
        path.lineTo(QPointF(x, y + (4 if i % 2 else -4)))
    painter.drawPath(path)

    # 小箭头（更靠右）
    path = QPainterPath(QPointF(width - 40, 64))
    path.lineTo(QPointF(width - 22, 50))
    path.moveTo(QPointF(width - 32, 52))
    path.lineTo(QPointF(width - 22, 50))
    path.lineTo(QPointF(width - 26, 60))
    painter.drawPath(path)


def _cos(rad: float) -> float:
    import math
    return math.cos(rad)


def _sin(rad: float) -> float:
    import math
    return math.sin(rad)


def draw_hard_shadow(
    painter: QPainter,
    rect: QRectF,
    offset=QPoint(2, 3),
    color: str = SHADOW,
    radius: float = 8.0,
):
    """硬边投影：把纸面整体挪开一点画一块实色，没有模糊。"""
    painter.save()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawRoundedRect(rect.translated(offset), radius, radius)
    painter.restore()


def hard_shadow(widget, offset=QPoint(2, 2), color: str = SHADOW):
    """给一个控件挂上“硬边”投影（无模糊，像纸片投下的影子）。"""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(0)
    effect.setOffset(offset)
    effect.setColor(QColor(color))
    widget.setGraphicsEffect(effect)


def draw_sketch_rect(
    painter: QPainter,
    rect: QRectF,
    color: str = PENCIL,
    wobble: float = 1.1,
    pen_width: float = 1.4,
):
    """画一个四条边略抖动的矩形，模拟人手画的边框。

    抖动幅度由矩形坐标决定：同一个矩形每次重绘都一样，
    不会因为闪烁而乱跳。
    """
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(color), pen_width))

    seed = int(rect.x() * 7 + rect.y() * 13)
    rng = random.Random(seed)

    def j():
        return rng.uniform(-wobble, wobble)

    x0, y0, x1, y1 = rect.left(), rect.top(), rect.right(), rect.bottom()
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    points = [
        QPointF(x0 + j(), y0 + j()),
        QPointF(mx + j(), y0 + j() * 1.4),
        QPointF(x1 + j(), y0 + j()),
        QPointF(x1 + j(), my + j() * 1.4),
        QPointF(x1 + j(), y1 + j()),
        QPointF(mx + j(), y1 + j() * 1.4),
        QPointF(x0 + j(), y1 + j()),
        QPointF(x0 + j(), my + j() * 1.4),
    ]
    path = QPainterPath(points[0])
    for point in points[1:]:
        path.lineTo(point)
    path.closeSubpath()
    painter.drawPath(path)
    painter.restore()
