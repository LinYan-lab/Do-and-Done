"""完整月历视图：6 行 7 列的日期网格，可翻月、可点选日期。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from calendar_todo.logic import date_utils
from calendar_todo.logic import completion
from calendar_todo.logic import holidays
from calendar_todo.ui import theme
from calendar_todo.ui.day_cell import DayCell


class MonthView(QWidget):
    date_selected = Signal(object)  # 选中/取消选中某天时发出（None 表示取消）

    def __init__(self, repo):
        super().__init__()
        self._repo = repo
        self._year = date_utils.today().year
        self._month = date_utils.today().month
        self._selected = None
        self._cells: dict = {}
        self._memorial_mode = False

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 10)
        root.setSpacing(8)

        # ---- 顶部：翻月按钮 + 标题 + 回今天 ----
        header = QHBoxLayout()
        header.setSpacing(6)

        prev_btn = self._make_nav_button("◀")
        next_btn = self._make_nav_button("▶")
        prev_btn.clicked.connect(self.go_prev)
        next_btn.clicked.connect(self.go_next)

        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:{theme.INK};"
        )

        today_btn = QPushButton("今天")
        today_btn.setStyleSheet(theme.LIGHT_BUTTON)
        today_btn.clicked.connect(self.go_today)

        header.addWidget(prev_btn)
        header.addWidget(self.title_label, 1)
        header.addWidget(next_btn)
        header.addWidget(today_btn)

        # ---- 日期网格 ----
        self._grid = QGridLayout()
        self._grid.setSpacing(4)
        for col, name in enumerate(date_utils.WEEKDAY_NAMES):
            label = QLabel(name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"color:{theme.INK_SOFT}; font-size:12px;")
            self._grid.addWidget(label, 0, col)

        root.addLayout(header)
        root.addLayout(self._grid)
        self._rebuild()

    # ---------- 对外操作 ----------

    def go_prev(self):
        self._year, self._month = date_utils.shift_month(self._year, self._month, -1)
        self._selected = None
        self._rebuild()
        self.date_selected.emit(None)

    def go_next(self):
        self._year, self._month = date_utils.shift_month(self._year, self._month, 1)
        self._selected = None
        self._rebuild()
        self.date_selected.emit(None)

    def go_today(self):
        self._year = date_utils.today().year
        self._month = date_utils.today().month
        self._selected = None
        self._rebuild()
        self.date_selected.emit(None)

    # ---------- 内部实现 ----------

    def _rebuild(self):
        """按当前年月重画 42 个日期格子。"""
        # 先清掉旧格子（第 0 行是星期表头，保留）
        while self._grid.count() > 7:
            item = self._grid.takeAt(7)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._cells = {}
        self.title_label.setText(date_utils.month_title(self._year, self._month))
        today = date_utils.today()
        grid = date_utils.month_grid(self._year, self._month)
        stats = self._repo.stats_for_range(grid[0], grid[-1])

        for i, day in enumerate(grid):
            row, col = divmod(i, 7)
            cell = DayCell(
                day,
                is_today=(day == today),
                in_current_month=(day.month == self._month),
            )
            cell.set_completion_color(self._color_for(day, stats))
            cell.clicked.connect(self._on_cell_clicked)
            self._grid.addWidget(cell, row + 1, col)
            self._cells[day] = cell
        self.refresh_memorials()

    def goto(self, year: int, month: int):
        """直接跳到某年某月（测试和外部跳转用）。"""
        self._year = year
        self._month = month
        self._selected = None
        self._rebuild()
        self.date_selected.emit(None)

    def set_mode(self, memorial_mode: bool):
        """切换待办/纪念日模式：控制格子上是否显示节日和纪念日小字。"""
        self._memorial_mode = memorial_mode
        self.refresh_memorials()

    def refresh_memorials(self):
        """重新读取节日/纪念日，更新每个格子下方的小字。"""
        grid = date_utils.month_grid(self._year, self._month)
        if self._memorial_mode:
            holidays_map = holidays.holidays_for_range(grid[0], grid[-1])
            memorials_map = self._repo.memorials_for_range(grid[0], grid[-1])
        else:
            holidays_map = {}
            memorials_map = {}
        for day, cell in self._cells.items():
            # 格子很小，只显示一个名字：自定义纪念日优先，其次节日
            names = list(
                dict.fromkeys(memorials_map.get(day, []) + holidays_map.get(day, []))
            )
            cell.set_sub_text(names[0] if names else "")

    def refresh_colors(self):
        """任务数据变化后，重新读取完成率并更新所有格子颜色。"""
        grid = date_utils.month_grid(self._year, self._month)
        stats = self._repo.stats_for_range(grid[0], grid[-1])
        for day, cell in self._cells.items():
            cell.set_completion_color(self._color_for(day, stats))

    def _color_for(self, day, stats):
        """查某一天的统计，交给逻辑层算出该染的颜色（可能为 None）。"""
        done, total = stats.get(day, (0, 0))
        return completion.day_color(done, total, day)

    def _on_cell_clicked(self, day):
        """点选/取消选中某一天，并同步所有格子的选中样式。"""
        self._selected = None if self._selected == day else day
        for cell_day, cell in self._cells.items():
            cell.set_selected(cell_day == self._selected)
        self.date_selected.emit(self._selected)

    @staticmethod
    def _make_nav_button(text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(30, 30)
        btn.setStyleSheet(theme.NAV_BUTTON)
        return btn
