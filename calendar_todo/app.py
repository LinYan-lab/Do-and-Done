"""应用与主窗口。

阶段 0：只做一个能弹出的最小窗口，用来验证环境是否可用。
阶段 1：在这里实现悬浮条、滚动日历和月历的展开/折叠。
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget


class MainWindow(QWidget):
    """阶段 0 的最小验证窗口。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("日历 + ToDo List")
        self.resize(320, 160)

        layout = QVBoxLayout(self)
        label = QLabel("阶段 0 完成：Qt 环境可以正常运行了")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)


def main() -> int:
    """创建应用、显示窗口并进入事件循环。"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()
