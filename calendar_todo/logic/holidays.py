"""内置节假日：固定公历节日 + 农历节日换算 + 清明近似计算。"""

from datetime import date

from zhdate import ZhDate

# 固定公历节日
_FIXED_HOLIDAYS = {
    (1, 1): "元旦",
    (5, 1): "劳动节",
    (10, 1): "国庆节",
    (10, 2): "国庆节",
    (10, 3): "国庆节",
}

# 按农历计算的节日：(农历月, 农历日)
_LUNAR_HOLIDAYS = {
    (1, 1): "春节",
    (1, 15): "元宵节",
    (5, 5): "端午节",
    (8, 15): "中秋节",
    (9, 9): "重阳节",
}


def holidays_in_year(year: int) -> dict[date, str]:
    """某一年所有内置节假日的公历日期。"""
    result = {}
    for (month, day), name in _FIXED_HOLIDAYS.items():
        result[date(year, month, day)] = name
    for (month, day), name in _LUNAR_HOLIDAYS.items():
        try:
            solar = ZhDate(year, month, day).to_datetime().date()
        except (ValueError, TypeError):
            continue
        result[solar] = name
    result[date(year, 4, _qingming_day(year))] = "清明节"
    return result


def holidays_for_range(start: date, end: date) -> dict[date, list[str]]:
    """一段日期范围内所有内置节假日：{日期: [节日名, ...]}。"""
    result: dict[date, list[str]] = {}
    for year in range(start.year, end.year + 1):
        for day, name in holidays_in_year(year).items():
            if start <= day <= end:
                result.setdefault(day, []).append(name)
    return result


def _qingming_day(year: int) -> int:
    """清明节在 4 月的哪一天（近似算法，常见年份误差不超过一天）。"""
    y = year % 100
    return int(y * 0.2422 + 4.81) - int(y / 4)
