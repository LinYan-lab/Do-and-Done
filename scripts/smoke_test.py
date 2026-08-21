"""冒烟测试：在无界面模式下验证程序能启动、按钮/面板能工作。

用法：
    QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/smoke_test.py
"""

import sys
from datetime import date
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QPointF, QSettings, Qt
from PySide6.QtGui import QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QApplication

# 让 Python 能找到项目根目录下的 calendar_todo 包：
# 脚本在 scripts/ 里运行时，默认搜索路径只有 scripts/ 本身，
# 需要手动把上一层目录（项目根目录）加进去。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from calendar_todo.app import CalendarApp
from calendar_todo.logic import date_utils


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
    # 切回滚动日历模式：滚动条的交互测试必须在可见状态下进行，
    # 隐藏时滚动区域的尺寸更新是滞后的，会干扰测试结果
    calendar.panel.toggle_mode()
    app.processEvents()
    assert calendar.panel.current_mode == calendar.panel.MODE_STRIP, "切回后应该是滚动日历模式"

    # ---- 日期工具（纯计算，不依赖界面）----
    assert len(date_utils.month_grid(2026, 8)) == 42, "月历应固定显示 42 天"
    assert date_utils.month_grid(2026, 8)[0].weekday() == 0, "月历应从周一开始"
    assert date_utils.days_in_month(2024, 2) == 29, "2024 是闰年，2 月应有 29 天"
    assert date_utils.shift_month(2026, 1, -1) == (2025, 12), "跨年翻月应正确"

    # ---- 月历翻页 ----
    title_before = calendar.panel.month_view.title_label.text()
    calendar.panel.month_view.go_next()
    app.processEvents()
    title_after = calendar.panel.month_view.title_label.text()
    assert title_before != title_after, "翻月后标题应该变化"

    # ---- 滚动条翻页 ----
    strip_title_before = calendar.panel.strip_view.title_label.text()
    calendar.panel.strip_view.go_next()
    app.processEvents()
    assert calendar.panel.strip_view.title_label.text() != strip_title_before, "滚动条翻页后标题应该变化"

    # ---- 模拟真实滚轮：事件发给日期格子（而不是视口），应滚向更晚的日期 ----
    strip = calendar.panel.strip_view
    viewport = strip.scroll_area.viewport()
    hbar = strip.scroll_area.horizontalScrollBar()
    value_before = hbar.value()
    wheel_event = QWheelEvent(
        QPointF(10, 10),
        QPointF(10, 10),
        QPoint(0, 0),
        QPoint(0, -120),  # 角度增量：向下滚一格
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QApplication.sendEvent(strip.row_layout.itemAt(0).widget(), wheel_event)
    app.processEvents()
    assert hbar.value() > value_before, "滚轮下滚应显示更晚的日期"

    # ---- 模拟真实拖动：在日期格子上按下，向左拖 40 像素，滚动值应变大 ----
    value_before = hbar.value()
    press = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(100, 20),
        QPointF(100, 20),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    move = QMouseEvent(
        QEvent.Type.MouseMove,
        QPointF(60, 20),
        QPointF(60, 20),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    release = QMouseEvent(
        QEvent.Type.MouseButtonRelease,
        QPointF(60, 20),
        QPointF(60, 20),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(strip.row_layout.itemAt(0).widget(), press)
    QApplication.sendEvent(viewport, move)
    QApplication.sendEvent(viewport, release)
    app.processEvents()
    assert hbar.value() > value_before, "向左拖动应显示更晚的日期"

    # ---- 无限滚动：向下滚 80 格，应能滚出最初的 30 天范围 ----
    strip = calendar.panel.strip_view
    hbar = strip.scroll_area.horizontalScrollBar()
    initial_max = hbar.maximum()
    initial_last = strip._days[-1]
    wheel_down = QWheelEvent(
        QPointF(10, 10),
        QPointF(10, 10),
        QPoint(0, 0),
        QPoint(0, -120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    for _ in range(80):
        QApplication.sendEvent(strip.row_layout.itemAt(15).widget(), wheel_down)
    app.processEvents()
    assert hbar.value() > initial_max, "应能滚出最初的 30 天范围"
    assert strip._days[-1] > initial_last, "右侧应自动补上更晚的日期"
    assert len(strip._days) <= 120, "天数不应无限累积"

    # ---- 无限滚动：回到最左端后继续向上滚，左侧也应能一直延伸 ----
    hbar.setValue(hbar.minimum())
    app.processEvents()
    initial_first = strip._days[0]
    wheel_up = QWheelEvent(
        QPointF(10, 10),
        QPointF(10, 10),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    for _ in range(40):
        QApplication.sendEvent(strip.row_layout.itemAt(15).widget(), wheel_up)
    app.processEvents()
    assert strip._days[0] < initial_first, "左侧应自动补上更早的日期"

    # 滚到很远之后，“回今天”仍应有效
    strip.go_today()
    app.processEvents()
    assert date_utils.today() in strip._days, "滚到很远后，今天应仍在列表里"

    print("冒烟测试通过：窗口联动、月历、滚动条、无限滚动、日期工具都正常。")
    calendar.quit()


if __name__ == "__main__":
    main()
