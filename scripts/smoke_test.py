"""冒烟测试：在无界面模式下验证程序能启动、按钮/面板能工作。

用法：
    QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/smoke_test.py
"""

import sys
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QSettings, Qt
from PySide6.QtGui import QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QApplication
from zhdate import ZhDate

# 让 Python 能找到项目根目录下的 calendar_todo 包：
# 脚本在 scripts/ 里运行时，默认搜索路径只有 scripts/ 本身，
# 需要手动把上一层目录（项目根目录）加进去。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from calendar_todo.app import CalendarApp
from calendar_todo.logic import date_utils
from calendar_todo.logic import completion
from calendar_todo.logic import holidays
from calendar_todo.ui.day_cell import DayCell


def main():
    # 把设置写到 /tmp，避免测试污染真实配置
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, "/tmp")

    # 测试用临时数据库，避免污染真实数据
    db_path = Path("/tmp") / "calendar_smoke_test.db"
    db_path.unlink(missing_ok=True)

    app = QApplication(sys.argv)
    calendar = CalendarApp(app, db_path=db_path)
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

    # ---- 模拟真实拖动：在可见格子上按下，向左拖 40 像素，滚动值应变大 ----
    pressed_cell = None
    press_point = None
    for i in range(strip.row_layout.count()):
        cell = strip.row_layout.itemAt(i).widget()
        cell_top_left = cell.mapTo(viewport, QPoint(0, 0))
        cell_rect = QRect(cell_top_left.x(), cell_top_left.y(), cell.width(), cell.height())
        if viewport.rect().intersects(cell_rect):
            pressed_cell = cell
            press_point = QPoint(
                max(cell_rect.x(), viewport.rect().left()) + 5,
                viewport.rect().center().y(),
            )
            break
    assert pressed_cell is not None, "视口里应有一个可见的日期格子"
    cell_press_pos = pressed_cell.mapFrom(viewport, press_point)

    value_before = hbar.value()
    press = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(cell_press_pos),
        QPointF(press_point),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    move_point = press_point - QPoint(40, 0)
    move = QMouseEvent(
        QEvent.Type.MouseMove,
        QPointF(move_point),
        QPointF(move_point),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    release = QMouseEvent(
        QEvent.Type.MouseButtonRelease,
        QPointF(move_point),
        QPointF(move_point),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(pressed_cell, press)
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

    # ---- 数据层：跨多日任务 ----
    repo = calendar.repo
    today = date_utils.today()
    task_id = repo.add_task("读三章书", today, today + timedelta(days=2))
    assert repo.stats_for_date(today) == (0, 0), "还没到结束日，不参与今天统计"
    assert repo.stats_for_date(today + timedelta(days=2)) == (0, 1), "结束当天才统计"
    assert repo.stats_for_date(today + timedelta(days=3)) == (0, 0), "范围外不应有任务"

    repo.set_done(task_id, today, True)
    assert repo.stats_for_date(today + timedelta(days=2)) == (0, 1), "中间天的勾选不影响结束日"
    repo.set_done(task_id, today + timedelta(days=2), True)
    assert repo.stats_for_date(today + timedelta(days=2)) == (1, 1), "结束日勾选后才算完成"

    repo.delete_task(task_id)
    assert repo.stats_for_date(today) == (0, 0), "删除任务后统计应归零"

    # ---- 任务视图：点日期进入任务页，返回后回到滚动日历 ----
    repo.add_task("买牛奶", today, today)
    calendar.panel.show_task(today)
    app.processEvents()
    assert calendar.panel.current_mode == calendar.panel.MODE_TASK, "应进入任务页"
    assert len(calendar.panel.task_view._rows) == 1, "任务页应显示 1 条任务"
    calendar.panel.task_view.back_button.click()
    app.processEvents()
    assert calendar.panel.current_mode == calendar.panel.MODE_STRIP, "返回后应回到滚动日历"

    # ---- 染色规则：逻辑层边界 ----
    assert completion.rate_color(1, 1) == completion.COLOR_BLUE, "100% 应为蓝色"
    assert completion.rate_color(3, 5) == completion.COLOR_GREEN, "60% 应为绿色"
    assert completion.rate_color(2, 5) == completion.COLOR_YELLOW, "40% 应为黄色"
    assert completion.rate_color(1, 5) == completion.COLOR_YELLOW, "20% 应为黄色"
    assert completion.rate_color(0, 1) == completion.COLOR_RED, "0% 应为红色"
    assert completion.day_color(1, 1, today + timedelta(days=1)) is None, "未来日期不染色"
    assert completion.day_color(0, 0, today) is None, "无任务日期不染色"

    # ---- 染色：日历格子反映完成率，且月历/滚动条同步 ----
    month_view = calendar.panel.month_view
    month_view.go_today()
    app.processEvents()
    today_cell = month_view._cells[today]
    assert today_cell._completion_color == completion.COLOR_RED, "有任务未完成应为红色"

    milk = repo.tasks_on(today)[0]
    repo.set_done(milk["id"], today, True)
    month_view.refresh_colors()
    assert today_cell._completion_color == completion.COLOR_BLUE, "100% 应为蓝色"

    strip.refresh_colors()
    strip_today_cell = None
    for i in range(strip.row_layout.count()):
        widget = strip.row_layout.itemAt(i).widget()
        if widget.day == today:
            strip_today_cell = widget
            break
    assert strip_today_cell is not None, "滚动条里应有今天的格子"
    assert (
        strip_today_cell._completion_color == completion.COLOR_BLUE
    ), "滚动条颜色应与月历同步"

    # ---- 跨日任务的中间天不染色：只统计结束日 ----
    yesterday = today - timedelta(days=1)
    repo.add_task("跨日中间天", yesterday, yesterday + timedelta(days=1))
    month_view.refresh_colors()
    if yesterday in month_view._cells:
        assert (
            month_view._cells[yesterday]._completion_color is None
        ), "中间天不应按跨日任务染色"

    # ---- 轻点滚动条里的日期：应选中并进入任务页（而不是拖动） ----
    click_cell = None
    click_point = None
    for i in range(strip.row_layout.count()):
        cell = strip.row_layout.itemAt(i).widget()
        top_left = cell.mapTo(viewport, QPoint(0, 0))
        cell_rect = QRect(top_left.x(), top_left.y(), cell.width(), cell.height())
        if viewport.rect().intersects(cell_rect):
            click_cell = cell
            click_point = QPoint(
                max(cell_rect.x(), viewport.rect().left()) + 5,
                viewport.rect().center().y(),
            )
            break
    assert click_cell is not None, "应能找到可见的日期格子"
    click_local = click_cell.mapFrom(viewport, click_point)
    click_press = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(click_local),
        QPointF(click_point),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    click_release = QMouseEvent(
        QEvent.Type.MouseButtonRelease,
        QPointF(click_point),
        QPointF(click_point),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(click_cell, click_press)
    QApplication.sendEvent(viewport, click_release)
    app.processEvents()
    assert calendar.panel.current_mode == calendar.panel.MODE_TASK, "轻点日期应进入任务页"
    assert strip._selected == click_cell.day, "轻点应选中该日期"

    # ---- 纪念日：数据层与农历换算 ----
    repo.add_memorial("妈妈的生日", 8, 15, is_lunar=True)
    mid_autumn = ZhDate(today.year, 8, 15).to_datetime().date()
    assert "妈妈的生日" in repo.memorials_on(mid_autumn), "农历纪念日应落到对应公历日"
    assert (
        holidays.holidays_in_year(mid_autumn.year).get(mid_autumn) == "中秋节"
    ), "农历八月十五应是中秋节"
    assert (
        holidays.holidays_in_year(today.year).get(date(today.year, 1, 1)) == "元旦"
    ), "元旦应是固定公历节日"
    repo.add_memorial("结婚纪念日", 6, 18, is_lunar=False)
    assert "结婚纪念日" in repo.memorials_on(date(today.year, 6, 18)), "公历纪念日应落在固定日期"

    # ---- 纪念日模式：格子上显示节日/纪念日名称 ----
    panel = calendar.panel
    panel.mode_button.click()
    app.processEvents()
    assert panel.memorial_mode, "应切换到纪念日模式"
    panel.month_view.goto(mid_autumn.year, mid_autumn.month)
    app.processEvents()
    mid_cell = panel.month_view._cells[mid_autumn]
    assert mid_cell.sub_label.text() == "妈妈的生日", "有纪念日时优先显示纪念日"

    panel.month_view.goto(today.year, 1)
    app.processEvents()
    assert (
        panel.month_view._cells[date(today.year, 1, 1)].sub_label.text() == "元旦"
    ), "没有纪念日时显示节日"
    panel.month_view.goto(mid_autumn.year, mid_autumn.month)
    app.processEvents()

    # 纪念日模式下点击日期，应进入纪念日页
    panel.month_view._on_cell_clicked(mid_autumn)
    app.processEvents()
    assert panel.current_mode == panel.MODE_MEMORIAL, "应进入纪念日页"
    assert len(panel.memorial_view._rows) == 1, "纪念日页应显示妈妈的生日"

    # 返回日历，切回待办模式
    panel.memorial_view.back_button.click()
    app.processEvents()
    assert panel.current_mode == panel.MODE_STRIP, "返回应回到日历"
    panel.mode_button.click()
    app.processEvents()
    assert not panel.memorial_mode, "应切回待办模式"

    # 删除纪念日后不再出现
    memorial = repo.memorial_rows_on(mid_autumn)[0]
    repo.delete_memorial(memorial["id"])
    assert "妈妈的生日" not in repo.memorials_on(mid_autumn), "删除后不应再出现"

    print("冒烟测试通过：窗口联动、月历、滚动条、无限滚动、数据层、任务页、染色同步都正常。")
    calendar.quit()


if __name__ == "__main__":
    main()
