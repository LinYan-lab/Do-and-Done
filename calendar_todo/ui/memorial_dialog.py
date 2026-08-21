"""添加纪念日对话框：名称 + 公历/农历 + 月/日（纪念日每年重复）。"""

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
)
from zhdate import ZhDate

from calendar_todo.ui import theme


class MemorialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加纪念日")
        self.setModal(True)
        self._values = None

        form = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("比如：妈妈的生日")

        self.lunar_check = QCheckBox("按农历（如农历生日）")

        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        self.day_spin = QSpinBox()
        self.day_spin.setRange(1, 31)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        form.addRow("名称", self.name_edit)
        form.addRow("类型", self.lunar_check)
        form.addRow("月份", self.month_spin)
        form.addRow("日期", self.day_spin)
        form.addRow(buttons)
        self.setStyleSheet(
            theme.INPUT_FIELD
            + "QCheckBox{color:#3B4252;}"
            "QCheckBox::indicator{width:16px; height:16px;}"
            + theme.DIALOG_BUTTONS
        )

    def _validate_and_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请填写纪念日名称")
            return
        month = self.month_spin.value()
        day = self.day_spin.value()
        if self.lunar_check.isChecked():
            try:
                ZhDate(2026, month, day)
            except (ValueError, TypeError):
                QMessageBox.warning(self, "提示", "这不是一个有效的农历日期")
                return
        else:
            try:
                date(2000, month, day)
            except ValueError:
                QMessageBox.warning(self, "提示", "这不是一个有效的公历日期")
                return
        self._values = (name, month, day, self.lunar_check.isChecked())
        self.accept()

    def values(self):
        return self._values
