"""纪念日视图：展示某一天会遇到的所有纪念日，支持添加和删除。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
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
from calendar_todo.ui.memorial_dialog import MemorialDialog

_NAV_BUTTON_STYLE = (
    "QPushButton{background:#EEF1F5; border:none; border-radius:7px;"
    " font-size:13px; color:#333333;}"
    "QPushButton:hover{background:#DFE5EC;}"
)


class MemorialView(QWidget):
    back_requested = Signal()  # 点“返回”时发出，让面板切回日历
    data_changed = Signal()    # 纪念日增删后发出，让日历刷新小字

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
        self.back_button.setStyleSheet(_NAV_BUTTON_STYLE)
        self.back_button.clicked.connect(self.back_requested)

        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#333333;"
        )

        add_button = QPushButton("＋添加")
        add_button.setStyleSheet(
            "QPushButton{background:#3D7BFF; color:white; border:none;"
            " border-radius:6px; padding:4px 10px; font-size:13px;}"
            "QPushButton:hover{background:#4D88FF;}"
        )
        add_button.clicked.connect(self._on_add)

        header.addWidget(self.back_button)
        header.addWidget(self.title_label, 1)
        header.addWidget(add_button)

        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("color:#888888; font-size:12px;")

        # ---- 列表 ----
        self.list_area = QScrollArea()
        self.list_area.setWidgetResizable(True)
        self.list_area.setFrameShape(QFrame.Shape.NoFrame)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch(1)
        self.list_area.setWidget(self.list_container)

        root.addLayout(header)
        root.addWidget(self.summary_label)
        root.addWidget(self.list_area, 1)

        self.set_date(date_utils.today())

    def set_date(self, day):
        """切换到某一天，重新加载这一天的纪念日。"""
        self._day = day
        self.title_label.setText(f"{day.month}月{day.day}日 纪念日")
        self._reload()

    def _reload(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._rows = []

        memorials = self._repo.memorial_rows_on(self._day)
        for memorial in memorials:
            row = self._make_row(memorial)
            self.list_layout.insertWidget(self.list_layout.count() - 1, row)
            self._rows.append(row)

        if memorials:
            self.summary_label.setText(f"共 {len(memorials)} 个纪念日")
        else:
            self.summary_label.setText("这一天没有自定义纪念日")

    def _make_row(self, memorial) -> QWidget:
        row = QWidget()
        row.setStyleSheet("background:#F5F7FA; border-radius:8px;")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 6, 6, 6)
        layout.setSpacing(8)

        name = QLabel(memorial["name"])
        name.setStyleSheet("background:transparent; color:#1F2937; font-size:14px;")

        badge = QLabel("农历" if memorial["is_lunar"] else "公历")
        badge.setStyleSheet(
            "background:#E8F0FE; color:#2D6CDF; border-radius:4px;"
            " padding:1px 6px; font-size:11px;"
        )

        delete_button = QPushButton("✕")
        delete_button.setFixedSize(24, 24)
        delete_button.setStyleSheet(
            "QPushButton{background:transparent; color:#999999; border:none;"
            " font-size:13px;}"
            "QPushButton:hover{background:#E74C3C; color:white; border-radius:6px;}"
        )

        layout.addWidget(name, 1)
        layout.addWidget(badge)
        layout.addWidget(delete_button)

        delete_button.clicked.connect(
            lambda _=False, memorial_id=memorial["id"]: self._on_delete(memorial_id)
        )
        return row

    def _on_add(self):
        dialog = MemorialDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, month, day, is_lunar = dialog.values()
            self._repo.add_memorial(name, month, day, is_lunar)
            self._reload()
            self.data_changed.emit()

    def _on_delete(self, memorial_id: int):
        self._repo.delete_memorial(memorial_id)
        self._reload()
        self.data_changed.emit()
