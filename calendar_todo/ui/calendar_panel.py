"""日历面板：悬浮按钮展开的容器，支持待办/纪念日两种模式，
以及“滚动日历”“完整月历”“任务页”“纪念日页”四种形态。
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from calendar_todo.ui.memorial_view import MemorialView
from calendar_todo.ui.month_view import MonthView
from calendar_todo.ui.strip_view import StripView
from calendar_todo.ui.task_view import TaskView


class _TitleBar(QFrame):
    """标题栏：显示标题和按钮，按住它可以直接拖动整个面板。"""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(38)
        self.setStyleSheet(
            "background:#2D6CDF;"
            "border-top-left-radius:10px;"
            "border-top-right-radius:10px;"
        )
        self._drag_offset = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        event.accept()


class CalendarPanel(QWidget):
    """无边框置顶面板：待办/纪念日模式 × 滚动日历/月历/详情页形态。"""

    MODE_STRIP = "strip"        # 滚动日历
    MODE_MONTH = "month"        # 完整月历
    MODE_TASK = "task"          # 任务页
    MODE_MEMORIAL = "memorial"  # 纪念日页

    date_selected = Signal(object)

    def __init__(self, repo):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setFixedWidth(380)
        self.setStyleSheet(
            "background:white; border:1px solid #d0d5dd; border-radius:10px;"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- 顶部标题栏 ----
        self.title_bar = _TitleBar()
        bar_layout = QHBoxLayout(self.title_bar)
        bar_layout.setContentsMargins(12, 0, 8, 0)
        bar_layout.setSpacing(8)

        title = QLabel("日历 ToDo")
        title.setStyleSheet("color:white; font-weight:bold; font-size:14px;")

        # 待办/纪念日模式切换按钮
        self.mode_button = QPushButton("纪念日模式")
        self.mode_button.setStyleSheet(
            "QPushButton{background:rgba(255,255,255,0.2); color:white; border:none;"
            " border-radius:5px; padding:4px 8px; font-size:12px;}"
            "QPushButton:hover{background:rgba(255,255,255,0.35);}"
        )

        self.toggle_button = QPushButton("展开月历")
        self.toggle_button.setStyleSheet(
            "QPushButton{background:#3D7BFF; color:white; border:none;"
            " border-radius:5px; padding:4px 10px;}"
            "QPushButton:hover{background:#4D88FF;}"
        )
        self.close_button = QPushButton("✕")
        self.close_button.setStyleSheet(
            "QPushButton{background:transparent; color:white; border:none;"
            " font-size:16px; padding:2px 8px;}"
            "QPushButton:hover{background:#C0392B; border-radius:5px;}"
        )

        bar_layout.addWidget(title)
        bar_layout.addStretch(1)
        bar_layout.addWidget(self.mode_button)
        bar_layout.addWidget(self.toggle_button)
        bar_layout.addWidget(self.close_button)

        # ---- 内容区：滚动日历 + 完整月历 + 任务页 + 纪念日页 ----
        self.stack = QStackedWidget()
        self.strip_view = StripView(repo)
        self.month_view = MonthView(repo)
        self.task_view = TaskView(repo)
        self.memorial_view = MemorialView(repo)
        self.stack.addWidget(self.strip_view)
        self.stack.addWidget(self.month_view)
        self.stack.addWidget(self.task_view)
        self.stack.addWidget(self.memorial_view)

        root.addWidget(self.title_bar)
        root.addWidget(self.stack)

        # ---- 信号连接 ----
        self.mode_button.clicked.connect(self.toggle_memorial_mode)
        self.toggle_button.clicked.connect(self.toggle_mode)
        self.close_button.clicked.connect(self.hide)
        self.strip_view.date_selected.connect(self.on_date_selected)
        self.month_view.date_selected.connect(self.on_date_selected)
        self.task_view.back_requested.connect(self._return_from_detail)
        self.task_view.data_changed.connect(self.refresh_colors)
        self.memorial_view.back_requested.connect(self._return_from_detail)
        self.memorial_view.data_changed.connect(self.refresh_memorials)

        # 当前是哪种模式、进入详情页之前处在哪种形态
        self._memorial_mode = False
        self._mode_before_detail = self.MODE_STRIP
        self._mode = self.MODE_STRIP
        self._apply_mode()

    # ---------- 只读状态 ----------

    @property
    def current_mode(self) -> str:
        """当前形态：MODE_STRIP / MODE_MONTH / MODE_TASK / MODE_MEMORIAL。"""
        return self._mode

    @property
    def memorial_mode(self) -> bool:
        """当前是不是纪念日模式。"""
        return self._memorial_mode

    # ---------- 模式切换 ----------

    def toggle_memorial_mode(self):
        """在待办模式和纪念日模式之间切换。"""
        self._memorial_mode = not self._memorial_mode
        self.mode_button.setText("待办模式" if self._memorial_mode else "纪念日模式")
        self.strip_view.set_mode(self._memorial_mode)
        self.month_view.set_mode(self._memorial_mode)

    def refresh_memorials(self):
        """纪念日数据变化后，让所有日历视图重新读取节日/纪念日小字。"""
        self.strip_view.refresh_memorials()
        self.month_view.refresh_memorials()

    def refresh_colors(self):
        """任务数据变化后，让所有日历视图同步刷新完成率颜色。"""
        self.strip_view.refresh_colors()
        self.month_view.refresh_colors()

    # ---------- 形态切换 ----------

    def show_strip(self):
        """以“滚动日历”形态显示面板。"""
        self._mode = self.MODE_STRIP
        self._apply_mode()
        self.show()

    def toggle_mode(self):
        """标题栏按钮：滚动日历 <-> 完整月历；详情页里则返回之前的形态。"""
        if self._mode in (self.MODE_TASK, self.MODE_MEMORIAL):
            self._mode = self._mode_before_detail
            self._apply_mode()
            return
        self._mode = self.MODE_MONTH if self._mode == self.MODE_STRIP else self.MODE_STRIP
        self._apply_mode()

    def show_task(self, day):
        """进入任务页，展示某一天的待办。"""
        if self._mode not in (self.MODE_TASK, self.MODE_MEMORIAL):
            self._mode_before_detail = self._mode
        self._mode = self.MODE_TASK
        self.task_view.set_date(day)
        self._apply_mode()

    def show_memorials(self, day):
        """进入纪念日页，展示某一天会遇到的所有纪念日。"""
        if self._mode not in (self.MODE_TASK, self.MODE_MEMORIAL):
            self._mode_before_detail = self._mode
        self._mode = self.MODE_MEMORIAL
        self.memorial_view.set_date(day)
        self._apply_mode()

    def _return_from_detail(self):
        """详情页点“返回”或标题栏按钮，回到进入前的形态。"""
        self._mode = self._mode_before_detail
        self._apply_mode()

    def on_date_selected(self, day):
        """用户在日历上点选某一天：按当前模式进入任务页或纪念日页。"""
        if day is not None:
            if self._memorial_mode:
                self.show_memorials(day)
            else:
                self.show_task(day)
            self.date_selected.emit(day)

    def _apply_mode(self):
        """根据当前形态切换显示页和面板高度。"""
        if self._mode == self.MODE_MONTH:
            self.stack.setCurrentIndex(1)
            self.setFixedHeight(430)
            self.toggle_button.setText("收起为滚动")
        elif self._mode in (self.MODE_TASK, self.MODE_MEMORIAL):
            self.stack.setCurrentIndex(2 if self._mode == self.MODE_TASK else 3)
            self.setFixedHeight(400)
            self.toggle_button.setText("返回日历")
        else:
            self.stack.setCurrentIndex(0)
            self.setFixedHeight(180)
            self.toggle_button.setText("展开月历")
