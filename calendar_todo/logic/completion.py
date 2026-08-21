"""完成率与染色规则：纯计算，不依赖界面，方便单独测试。"""

from datetime import date

# 四种完成率颜色（已确认的需求规则）
COLOR_BLUE = "#2D6CDF"    # x = 100%
COLOR_GREEN = "#34A853"   # 60% <= x < 100%
COLOR_YELLOW = "#F6C244"  # 20% <= x < 60%
COLOR_RED = "#E74C3C"     # 0% <= x < 20%


def rate_color(done: int, total: int):
    """按“已完成/总数”返回颜色；没有任务返回 None。"""
    if total <= 0:
        return None
    rate = done / total
    if rate >= 1.0:
        return COLOR_BLUE
    if rate >= 0.6:
        return COLOR_GREEN
    if rate >= 0.2:
        return COLOR_YELLOW
    return COLOR_RED


def day_color(done: int, total: int, day: date, today: date | None = None):
    """某一天该染的颜色：未来日期、无任务的日期不染色。"""
    if today is None:
        today = date.today()
    if total <= 0 or day > today:
        return None
    return rate_color(done, total)
