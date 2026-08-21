"""应用主程序：负责把各个窗口部件组装在一起，并管理它们之间的联动。

阶段 1：角落悬浮按钮 + 可展开/折叠的日历面板 + 系统托盘。
"""

import sys

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from calendar_todo.data.database import TodoRepository, default_db_path
from calendar_todo.ui import theme
from calendar_todo.ui.calendar_panel import CalendarPanel
from calendar_todo.ui.floating_button import FloatingButton


class CalendarApp:
    """整个程序的“总指挥”：持有按钮、面板和托盘，处理它们之间的联动。"""

    def __init__(self, qt_app: QApplication, db_path=None):
        self.qt_app = qt_app
        self.settings = QSettings("CalendarTodo", "CalendarTodo")

        # 数据库：默认存在 ~/.local/share/CalendarTodo/ 下
        self.repo = TodoRepository(db_path or default_db_path())

        # 两个界面部件
        self.button = FloatingButton()
        self.panel = CalendarPanel(self.repo)

        # 系统托盘（有的桌面环境没有托盘，不影响使用）
        self.tray = None
        self._init_tray()

        # 恢复上次记住的按钮位置
        self._restore_button_position()

        # 信号连接：点击按钮 -> 切换面板显示
        self.button.clicked.connect(self.on_button_clicked)

    # ---------- 系统托盘 ----------

    def _init_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("提示：当前环境没有系统托盘，仅使用悬浮按钮。")
            return

        self.tray = QSystemTrayIcon(self._make_tray_icon())
        self.tray.setToolTip("日历 ToDo")

        menu = QMenu()
        toggle_action = menu.addAction("显示/隐藏悬浮按钮")
        toggle_action.triggered.connect(self.toggle_button)
        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(self.quit)
        self.tray.setContextMenu(menu)

        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def on_tray_activated(self, reason):
        # 单击托盘图标：显示/隐藏悬浮按钮
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_button()

    @staticmethod
    def _make_tray_icon() -> QIcon:
        """用代码画一个简单图标，避免依赖图片文件。"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # 手绘纸片：纸面 + 墨色描边 + 手写“日”
        painter.setBrush(QColor(theme.PAPER))
        painter.setPen(QPen(QColor(theme.INK), 2))
        painter.drawRoundedRect(2, 2, 60, 60, 12, 12)

        painter.setPen(QColor(theme.INK))
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(28)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "日")
        painter.end()
        return QIcon(pixmap)

    # ---------- 悬浮按钮 ----------

    def on_button_clicked(self):
        """点击悬浮按钮：如果面板开着就收起，否则在按钮旁边打开滚动日历。"""
        if self.panel.isVisible():
            self.panel.hide()
            return
        self._place_panel_near_button()
        self.panel.show_strip()
        self.panel.raise_()
        self.panel.activateWindow()

    def toggle_button(self):
        """托盘菜单用的：显示/隐藏悬浮按钮（隐藏时同时收起面板）。"""
        if self.button.isVisible():
            self.button.hide()
            self.panel.hide()
        else:
            self.button.show()
            self.button.raise_()

    # ---------- 位置管理 ----------

    def _place_panel_near_button(self):
        """把面板放在按钮旁边；靠近屏幕右缘时自动改到左侧，防止超出屏幕。"""
        screen = QGuiApplication.primaryScreen().availableGeometry()

        x = self.button.x() + self.button.width() + 6
        if x + self.panel.width() > screen.right():
            x = self.button.x() - self.panel.width() - 6
        x = max(screen.left(), min(x, screen.right() - self.panel.width()))

        y = self.button.y() + self.button.height() - self.panel.height()
        y = max(screen.top(), min(y, screen.bottom() - self.panel.height()))

        self.panel.move(x, y)

    def _restore_button_position(self):
        """读取上次保存的位置；第一次运行放在屏幕右下角。"""
        x = int(self.settings.value("button_x", -1))
        y = int(self.settings.value("button_y", -1))
        if x < 0 or y < 0:
            screen = QGuiApplication.primaryScreen().availableGeometry()
            x = screen.right() - self.button.width() - 24
            y = screen.bottom() - self.button.height() - 24
        self.button.move(x, y)

    def quit(self):
        """退出前记住按钮位置，然后关闭程序。"""
        self.settings.setValue("button_x", self.button.x())
        self.settings.setValue("button_y", self.button.y())
        self.repo.close()
        self.qt_app.quit()


def main() -> int:
    """程序入口：创建应用、组装部件、进入事件循环。"""
    qt_app = QApplication(sys.argv)
    # 应用名用于数据/配置目录，保持英文；窗口里的中文标题不受影响
    qt_app.setApplicationName("CalendarTodo")
    qt_app.setOrganizationName("CalendarTodo")
    # 全局使用手写字体（系统没有时 Qt 会自动回退到无衬线）
    qt_app.setFont(QFont(theme.FONT_HAND, 10))
    # 关掉所有窗口时程序不应退出，因为系统托盘还在
    qt_app.setQuitOnLastWindowClosed(False)

    app = CalendarApp(qt_app)
    app.button.show()
    return qt_app.exec()
