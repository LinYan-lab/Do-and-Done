"""冒烟测试：在无界面模式下验证程序能启动、按钮/面板能工作。

用法：
    QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/smoke_test.py
"""

import sys
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

# 让 Python 能找到项目根目录下的 calendar_todo 包：
# 脚本在 scripts/ 里运行时，默认搜索路径只有 scripts/ 本身，
# 需要手动把上一层目录（项目根目录）加进去。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from calendar_todo.app import CalendarApp


def main():
    # 把设置写到 /tmp，避免测试污染真实配置
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "/tmp")

    app = QApplication(sys.argv)
    calendar = CalendarApp(app)
    calendar.button.show()
    app.processEvents()
    assert calendar.button.isVisible(), "悬浮按钮应该可见"

    calendar.on_button_clicked()
    app.processEvents()
    assert calendar.panel.isVisible(), "点击按钮后面板应该显示"
    assert calendar.panel.current_mode == calendar.panel.MODE_STRIP, "默认应该是滚动日历模式"

    calendar.panel.toggle_mode()
    app.processEvents()
    assert calendar.panel.current_mode == calendar.panel.MODE_MONTH, "切换后应该是完整月历模式"

    print("冒烟测试通过：按钮、面板、模式切换都正常。")
    calendar.quit()


if __name__ == "__main__":
    main()
