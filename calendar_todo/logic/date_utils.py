"""日期计算工具：月历排版、翻月、今天等，与界面完全无关。"""

import calendar
from datetime import date, timedelta

# 周一开头的星期名（和中国人的习惯一致）
WEEKDAY_NAMES = ["一", "二", "三", "四", "五", "六", "日"]


def today() -> date:
    """今天的日期。"""
    return date.today()


def days_in_month(year: int, month: int) -> int:
    """某个月有多少天（自动处理大小月和闰年）。"""
    return calendar.monthrange(year, month)[1]


def month_title(year: int, month: int) -> str:
    """月历标题，如 2026年8月。"""
    return f"{year}年{month}月"


def month_grid(year: int, month: int) -> list[date]:
    """返回月历要展示的日期：从该月第一个周一开始，共 42 天（6 行 7 列）。

    6 行是固定画法：不管这个月有没有 6 周，都画满，
    这样切换月份时日历不会上下跳动。
    """
    first_day = date(year, month, 1)
    start = first_day - timedelta(days=first_day.weekday())
    return [start + timedelta(days=i) for i in range(42)]


def shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    """把月份平移 delta 个月，自动处理跨年。

    例如 (2026, 1) 平移 -1 得到 (2025, 12)。
    """
    index = month - 1 + delta
    return year + index // 12, index % 12 + 1
