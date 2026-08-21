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
from calendar_todo.ui.day_cell import DayCell


class MonthView(QWidget):
    date_selected = Signal(object)  # 选中/取消选中某天时发出（None 表示取消）

    def __init__(self):
        super().__init__()
        self._year = date_utils.today().year
        self._month = date_utils.today().month
        self._selected = None
        self._cells: dict = {}

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
            "font-size:15px; font-weight:bold; color:#333333;"
        )

        today_btn = QPushButton("今天")
        today_btn.setStyleSheet(
            "QPushButton{background:#EEF1F5; color:#333333; border:none;"
            " border-radius:6px; padding:4px 10px; font-size:13px;}"
            "QPushButton:hover{background:#DFE5EC;}"
        )
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
            label.setStyleSheet("color:#888888; font-size:12px;")
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

        for i, day in enumerate(date_utils.month_grid(self._year, self._month)):
            row, col = divmod(i, 7)
            cell = DayCell(
                day,
                is_today=(day == today),
                in_current_month=(day.month == self._month),
            )
            cell.clicked.connect(self._on_cell_clicked)
            self._grid.addWidget(cell, row + 1, col)
            self._cells[day] = cell

    def _on_cell_clicked(self, day):
        """点选/取消选中某一天，并同步所有格子的选中样式。"""
        self._selected = None if self._selected == day else day
        for cell_day, cell in self._cells.items():
            cell.set_selected(cell_day == self._selected)
        self.date_selected.emit(self._selected)

    @staticmethod
    def _make_nav_button(text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(28, 28)
        btn.setStyleSheet(
            "QPushButton{background:#EEF1F5; border:none; border-radius:7px;"
            " font-size:13px; color:#333333;}"
            "QPushButton:hover{background:#DFE5EC;}"
        )
        return btn
