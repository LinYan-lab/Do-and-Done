"""添加任务的对话框：标题 + 开始日期 + 结束日期（支持跨多日）。"""

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
)


class TaskDialog(QDialog):
    def __init__(self, default_date: date, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加任务")
        self.setModal(True)
        self._values = None

        form = QFormLayout(self)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("要做什么？")

        self.start_edit = QDateEdit()
        self.end_edit = QDateEdit()
        for edit in (self.start_edit, self.end_edit):
            edit.setCalendarPopup(True)
            edit.setDisplayFormat("yyyy-MM-dd")
            edit.setDate(QDate(default_date.year, default_date.month, default_date.day))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        form.addRow("标题", self.title_edit)
        form.addRow("开始日期", self.start_edit)
        form.addRow("结束日期", self.end_edit)
        form.addRow(buttons)

    def _validate_and_accept(self):
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "提示", "请填写任务标题")
            return
        start = self.start_edit.date().toPython()
        end = self.end_edit.date().toPython()
        if end < start:
            QMessageBox.warning(self, "提示", "结束日期不能早于开始日期")
            return
        self._values = (title, start, end)
        self.accept()

    def values(self):
        return self._values
