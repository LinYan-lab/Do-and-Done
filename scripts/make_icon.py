"""生成应用图标 assets/icon.png（手绘便签风格，代码绘制，无图片依赖）。"""

import sys
from pathlib import Path

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPixmap

# 让脚本能导入项目里的 calendar_todo 包（scripts/ 不在默认搜索路径里）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from calendar_todo.ui import theme


def main():
    app = QGuiApplication(sys.argv)

    size = 128
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 便签整体歪 2 度
    painter.save()
    painter.translate(size / 2, size / 2)
    painter.rotate(-2)
    painter.translate(-size / 2, -size / 2)

    rect = QRectF(8, 8, size - 16, size - 16)
    theme.draw_hard_shadow(painter, rect, QPoint(5, 6), theme.SHADOW, 18)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(theme.STICKY_YELLOW))
    painter.drawRoundedRect(rect, 18, 18)
    theme.draw_sketch_rect(painter, rect, theme.INK, wobble=2.2, pen_width=3)

    font = QFont(theme.FONT_HAND, 58)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(theme.INK))
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "日")

    painter.restore()
    painter.end()

    output = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    ok = pixmap.save(str(output))
    print(f"图标已生成：{output}（{'成功' if ok else '失败'}）")


if __name__ == "__main__":
    main()
