"""任务视图：展示某一天的待办，支持勾选完成、添加任务、删除任务。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from calendar_todo.logic import date_utils
from calendar_todo.ui import theme
from calendar_todo.ui.task_dialog import TaskDialog


class TaskView(QWidget):
    back_requested = Signal()  # 点“返回”时发出，让面板切回日历
    data_changed = Signal()    # 任务增删改后发出，让日历刷新颜色

    def __init__(self, repo):
        super().__init__()
        self._repo = repo
        self._day = date_utils.today()
        self._rows = []

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 10)
        root.setSpacing(8)

        # ---- 头部：返回 + 标题 + 添加 ----
        header = QHBoxLayout()
        header.setSpacing(6)

        self.back_button = QPushButton("←")
        self.back_button.setFixedSize(28, 28)
        self.back_button.setStyleSheet(theme.NAV_BUTTON)
        self.back_button.clicked.connect(self.back_requested)

        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{theme.INK};"
        )

        add_button = QPushButton("＋添加")
        add_button.setStyleSheet(theme.PRIMARY_BUTTON)
        add_button.clicked.connect(self._on_add)

        header.addWidget(self.back_button)
        header.addWidget(self.title_label, 1)
        header.addWidget(add_button)

        self.summary_label = QLabel()
        self.summary_label.setStyleSheet(
            f"color:{theme.INK_SOFT}; font-size:12px;"
        )

        # ---- 任务列表（可滚动） ----
        self.list_area = QScrollArea()
        self.list_area.setWidgetResizable(True)
        self.list_area.setFrameShape(QFrame.Shape.NoFrame)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch(1)  # 底部留白，任务从上往下排
        self.list_area.setWidget(self.list_container)

        root.addLayout(header)
        root.addWidget(self.summary_label)
        root.addWidget(self.list_area, 1)

        self.set_date(date_utils.today())

    # ---------- 对外操作 ----------

    def set_date(self, day):
        """切换到某一天，重新加载这一天的任务。"""
        self._day = day
        self.title_label.setText(f"{day.month}月{day.day}日 待办")
        self._reload()

    # ---------- 内部实现 ----------

    def _reload(self):
        """清空列表，从数据库重新读取当天的任务。"""
        # 第一项是底部留白的 stretch，从第 0 项开始清
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._rows = []

        tasks = self._repo.tasks_on(self._day)
        for task in tasks:
            row = self._make_row(task)
            self.list_layout.insertWidget(self.list_layout.count() - 1, row)
            self._rows.append(row)
        self._update_summary()

    def _update_summary(self):
        done, total = self._repo.stats_for_date(self._day)
        if total == 0:
            self.summary_label.setText("今日没有到期任务")
        else:
            self.summary_label.setText(f"今日到期：已完成 {done}/{total}")

    def _make_row(self, task) -> QWidget:
        row = QWidget()
        row.setStyleSheet(
            f"background:{theme.STICKY_YELLOW};"
            f" border:2px dashed {theme.PENCIL}; border-radius:8px;"
        )
        theme.hard_shadow(row)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 6, 6, 6)
        layout.setSpacing(8)

        checkbox = QCheckBox()
        checkbox.setChecked(bool(task["done"]))
        title = QLabel(task["title"])
        title.setStyleSheet(
            f"background:transparent; color:{theme.INK}; font-size:14px;"
        )
        delete_button = QPushButton("✕")
        delete_button.setFixedSize(24, 24)
        delete_button.setStyleSheet(theme.DANGER_ICON)

        layout.addWidget(checkbox)
        layout.addWidget(title, 1)
        layout.addWidget(delete_button)

        # 先 setChecked 再连接信号，避免加载时就误触发一次
        checkbox.toggled.connect(
            lambda checked, task_id=task["id"]: self._on_toggled(task_id, checked)
        )
        delete_button.clicked.connect(
            lambda _=False, task_id=task["id"]: self._on_delete(task_id)
        )
        return row

    def _on_toggled(self, task_id: int, checked: bool):
        self._repo.set_done(task_id, self._day, checked)
        self._update_summary()
        self.data_changed.emit()

    def _on_delete(self, task_id: int):
        self._repo.delete_task(task_id)
        self._reload()
        self.data_changed.emit()

    def _on_add(self):
        dialog = TaskDialog(self._day, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, start, end = dialog.values()
            self._repo.add_task(title, start, end)
            self._reload()
            self.data_changed.emit()
