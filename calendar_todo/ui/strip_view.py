"""滚动日历条：横向展示一段连续日期，支持鼠标滚轮和按住拖动左右查看。"""

from datetime import timedelta

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from calendar_todo.logic import date_utils
from calendar_todo.ui.day_cell import DayCell

CELL_WIDTH = 52          # 一个格子多宽
CELL_HEIGHT = 56         # 一个格子多高
CELL_SPACING = 6         # 格子间距
CELL_STEP = CELL_WIDTH + CELL_SPACING  # 相邻格子中心的距离，拖动/滚动按它换算
DAY_COUNT = 30           # 预渲染 30 天，左右都有余量，滚动时不会露出空白
EXTEND_DAYS = 30         # 快到边缘时，一次补这么多天
EXTEND_MARGIN = 2 * CELL_STEP  # 距离边缘不到 2 个格子就触发补天
MAX_DAYS = 120           # 最多保留多少天，超出就把远处的清掉，防止无限累积


class StripView(QWidget):
    date_selected = Signal(object)

    def __init__(self):
        super().__init__()
        today = date_utils.today()
        # 30 天从“今天所在周一往前推 11 天”开始，保证今天在中间偏左，
        # 左右两边都有可滚动的余地
        self._days = [
            today - timedelta(days=today.weekday() + 11) + timedelta(days=i)
            for i in range(DAY_COUNT)
        ]
        self._selected = None

        # 拖动状态：按下位置、按下时的滚动值、是否已经进入拖动
        self._press_pos = None
        self._press_cell = None
        self._press_value = 0
        self._dragged = False
        # 滚轮小刻度累加（有的环境一格只发 ±1，直接取整会变成 0）
        self._wheel_accum = 0.0
        # 首次显示时才把今天滚到最左边（那时滚动范围才算得出来）
        self._positioned_once = False
        # 补天/清理进行中的标记，防止 setValue 触发的事件循环递归
        self._extending = False

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 10)
        root.setSpacing(8)

        # ---- 顶部：翻页按钮 + 标题 + 回今天 ----
        header = QHBoxLayout()
        header.setSpacing(6)

        prev_btn = self._make_nav_button("◀")
        next_btn = self._make_nav_button("▶")
        prev_btn.clicked.connect(self.go_prev)
        next_btn.clicked.connect(self.go_next)

        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size:14px; font-weight:bold; color:#333333;"
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

        # ---- 滚动区域：容器 + 固定像素宽度的格子行 ----
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setFixedHeight(CELL_HEIGHT)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.row = QWidget()
        self.row_layout = QHBoxLayout(self.row)
        self.row_layout.setContentsMargins(0, 0, 0, 0)
        self.row_layout.setSpacing(CELL_SPACING)
        self.scroll_area.setWidget(self.row)
        self._build_cells()

        # 鼠标在滚动区域上时显示“抓手”形状，提示可以拖动
        self.scroll_area.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
        self.scroll_area.viewport().setToolTip("滚轮或按住拖动查看日期")

        # 用事件过滤器接管鼠标事件：实现拖动和滚轮。
        # 每个日期格子和视口都装上过滤器，事件落在哪里就从哪里处理，
        # 不依赖“子控件把事件冒泡给父控件”的传递机制（那个在真实环境里不可靠）。
        self.scroll_area.viewport().installEventFilter(self)
        self.installEventFilter(self)

        # 滚动值变化时实时更新标题
        self.scroll_area.horizontalScrollBar().valueChanged.connect(self._update_title)

        root.addLayout(header)
        root.addWidget(self.scroll_area)

        # 初始定位：让今天出现在最左边，并刷新标题
        self.go_today()
        self._update_title()

    # ---------- 对外操作 ----------

    def go_prev(self):
        """向前翻 7 天（显示更早的日期）。"""
        self._shift_scroll(-7 * CELL_STEP)

    def go_next(self):
        """向后翻 7 天（显示更晚的日期）。"""
        self._shift_scroll(7 * CELL_STEP)

    def go_today(self):
        """滚动到今天。"""
        today = date_utils.today()
        index = self._days.index(today)
        hbar = self.scroll_area.horizontalScrollBar()
        hbar.setValue(hbar.minimum() + index * CELL_STEP)

    # ---------- 鼠标事件（事件过滤器） ----------

    def eventFilter(self, obj, event):
        etype = event.type()

        # 滚轮：视口、滚动条自身、以及每个日期格子都响应
        if etype == QEvent.Type.Wheel and (
            obj is self.scroll_area.viewport()
            or obj is self
            or isinstance(obj, DayCell)
        ):
            self._on_wheel(event)
            return True

        # 日期格子上的鼠标事件：在这里实现拖动和点击
        if isinstance(obj, DayCell):
            return self._handle_cell_mouse(obj, event)

        if obj is not self.scroll_area.viewport():
            return super().eventFilter(obj, event)

        if etype == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                # 用局部坐标而不是全局坐标：Wayland 下全局坐标经常是 (0,0)
                self._press_pos = event.position().toPoint()
                self._press_value = self.scroll_area.horizontalScrollBar().value()
                self._dragged = False
                # 吞掉按下事件：先记下状态，松开时再决定是“点击”还是“拖动”
                return True

        elif etype == QEvent.Type.MouseMove:
            if self._press_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
                delta_x = self._press_pos.x() - event.position().toPoint().x()
                if not self._dragged and abs(delta_x) > 5:
                    self._dragged = True  # 移动超过 5 像素，判定为拖动
                if self._dragged:
                    hbar = self.scroll_area.horizontalScrollBar()
                    self._ensure_range()
                    # 手指往哪边拖，日期就往哪边动（类似拖文件）
                    hbar.setValue(self._press_value + delta_x)
                    return True

        elif etype == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                was_dragged = self._dragged
                press = self._press_pos
                self._press_pos = None
                self._dragged = False
                # 没拖动才算“点击”，点中哪个格子就选中哪天
                if not was_dragged and press is not None:
                    cell = obj.childAt(event.position().toPoint())
                    if isinstance(cell, DayCell):
                        self._on_cell_clicked(cell.day)
                return True

        return super().eventFilter(obj, event)

    def _handle_cell_mouse(self, cell, event):
        """处理日期格子上的按下/移动/松开：区分点击和拖动。"""
        etype = event.type()

        if etype == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                # 局部坐标：Wayland 下全局坐标不可靠
                self._press_pos = event.position().toPoint()
                self._press_cell = cell
                self._press_value = self.scroll_area.horizontalScrollBar().value()
                self._dragged = False
                return True

        elif etype == QEvent.Type.MouseMove:
            if self._press_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
                delta_x = self._press_pos.x() - event.position().toPoint().x()
                if not self._dragged and abs(delta_x) > 5:
                    self._dragged = True
                if self._dragged:
                    hbar = self.scroll_area.horizontalScrollBar()
                    self._ensure_range()
                    hbar.setValue(self._press_value + delta_x)
                    return True

        elif etype == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                was_dragged = self._dragged
                pressed_cell = self._press_cell
                self._press_pos = None
                self._press_cell = None
                self._dragged = False
                # 没拖动才算“点击”，点中哪个格子就选中哪天
                if not was_dragged and pressed_cell is not None:
                    self._on_cell_clicked(pressed_cell.day)
                return True

        return super().eventFilter(cell, event)

    def _on_wheel(self, event):
        """滚轮上滚看更早的日期，下滚看更晚的日期。"""
        # 触控板/平滑滚轮会直接给像素增量，按像素滚最跟手
        pixel = event.pixelDelta()
        if not pixel.isNull():
            delta_px = pixel.y() if pixel.y() else pixel.x()
            self._shift_scroll(-delta_px)
            return

        # 普通滚轮给的是“刻度”增量：一格 120，上滚为正
        delta = event.angleDelta().y() or event.angleDelta().x()
        if delta == 0:
            return
        # 累加小数刻度：有的环境一格只发 ±1，直接取整会变成 0
        self._wheel_accum += delta / 120
        # 用 round 就近取整：int() 会把 -0.9999 截断成 0，导致永远滚不动
        notches = round(self._wheel_accum)
        if notches:
            self._wheel_accum -= notches
            self._shift_scroll(-notches * CELL_STEP)

    def showEvent(self, event):
        """首次显示、滚动范围算得出来时，把今天滚到最左边。"""
        super().showEvent(event)
        if not self._positioned_once:
            self._positioned_once = True
            self.go_today()

    # ---------- 内部实现 ----------

    def _build_cells(self):
        today = date_utils.today()
        for day in self._days:
            self.row_layout.addWidget(self._make_cell(day, today))
        # 明确告诉滚动区域内容行有多宽，否则滚动范围算不出来，滚不动
        self._update_row_width()

    def _shift_scroll(self, pixels: int):
        # 先检查是否需要补天：如果已经顶到边缘，setValue 不会生效，
        # 也就不会触发 valueChanged，必须提前把边缘扩出去
        hbar = self.scroll_area.horizontalScrollBar()
        hbar.setValue(hbar.value() + pixels)

    def _update_title(self):
        """根据当前滚动位置，算出左边缘附近可见的日期范围。"""
        # 快到边缘时先补上日期，保证永远滚不到头
        self._ensure_range()

        hbar = self.scroll_area.horizontalScrollBar()
        left_index = max(0, round(hbar.value() / CELL_STEP))
        visible_count = max(1, self.scroll_area.viewport().width() // CELL_STEP + 1)
        start = self._days[min(left_index, len(self._days) - 1)]
        end = self._days[min(left_index + visible_count - 1, len(self._days) - 1)]
        self.title_label.setText(
            f"{start.month}月{start.day}日 - {end.month}月{end.day}日"
        )

    # ---------- 无限滚动：快到边缘时自动补天 ----------

    def _ensure_range(self):
        """滚动接近边缘时，自动在对应方向补上日期。"""
        if self._extending:
            return
        hbar = self.scroll_area.horizontalScrollBar()
        if hbar.maximum() <= 0:
            return
        if hbar.value() > hbar.maximum() - EXTEND_MARGIN:
            self._extend_right()
        if hbar.value() < EXTEND_MARGIN:
            self._extend_left()

    def _extend_right(self):
        """在右侧补 30 天；如果天数太多，顺手清掉最左侧的。"""
        if self._extending:
            return
        self._extending = True
        today = date_utils.today()
        last = self._days[-1]
        for i in range(1, EXTEND_DAYS + 1):
            day = last + timedelta(days=i)
            self._days.append(day)
            self.row_layout.addWidget(self._make_cell(day, today))
        self._update_row_width()
        self._prune_left(today)
        self._extending = False

    def _extend_left(self):
        """在左侧补 30 天；滚动值也要往右推，让眼前的内容保持不动。"""
        if self._extending:
            return
        self._extending = True
        today = date_utils.today()
        first = self._days[0]
        new_days = [first - timedelta(days=i) for i in range(EXTEND_DAYS, 0, -1)]
        for index, day in enumerate(new_days):
            self.row_layout.insertWidget(index, self._make_cell(day, today))
        self._days = new_days + self._days
        self._update_row_width()

        # 内容行左边多了 30 个格子，滚动值要同步增大，否则眼前的内容会跳走
        hbar = self.scroll_area.horizontalScrollBar()
        hbar.setValue(hbar.value() + EXTEND_DAYS * CELL_STEP)
        self._press_value += EXTEND_DAYS * CELL_STEP

        self._prune_right(today)
        self._extending = False

    def _prune_left(self, today):
        """天数超上限时，从左侧清掉最早的日子（但保证今天还在）。"""
        overflow = min(len(self._days) - MAX_DAYS, self._days.index(today))
        if overflow <= 0:
            return
        for _ in range(overflow):
            item = self.row_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._days = self._days[overflow:]
        # 左边被清掉，剩下的内容整体左移，滚动值要同步减小
        hbar = self.scroll_area.horizontalScrollBar()
        hbar.setValue(hbar.value() - overflow * CELL_STEP)
        self._press_value -= overflow * CELL_STEP

    def _prune_right(self, today):
        """天数超上限时，从右侧清掉最晚的日子（但保证今天还在）。"""
        today_index = self._days.index(today)
        overflow = min(len(self._days) - MAX_DAYS, len(self._days) - 1 - today_index)
        if overflow <= 0:
            return
        for _ in range(overflow):
            item = self.row_layout.takeAt(self.row_layout.count() - 1)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._days = self._days[:-overflow]
        # 右边被清掉不影响眼前的显示，不用调滚动值

    def _update_row_width(self):
        """按当前天数刷新内容行宽度，滚动范围跟着变。"""
        self.row.setFixedSize(
            len(self._days) * CELL_WIDTH + (len(self._days) - 1) * CELL_SPACING,
            CELL_HEIGHT,
        )

    def _make_cell(self, day, today) -> DayCell:
        cell = DayCell(day, is_today=(day == today), in_current_month=True)
        cell.setFixedSize(CELL_WIDTH, CELL_HEIGHT)
        cell.installEventFilter(self)
        return cell

    def _on_cell_clicked(self, day):
        """点选/取消选中某一天，并同步所有格子的选中样式。"""
        self._selected = None if self._selected == day else day
        for i in range(self.row_layout.count()):
            cell = self.row_layout.itemAt(i).widget()
            if isinstance(cell, DayCell):
                cell.set_selected(cell.day == self._selected)
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
