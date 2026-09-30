import datetime
import calendar
from typing import List, Set

def _expand_field(field: str, min_val: int, max_val: int) -> Set[int]:
    """Expand a single cron field into the set of allowed integer values.
    Supports '*', lists (e.g. '1,2,3'), ranges (e.g. '1-5'), steps (e.g. '*/15' or '1-30/5')."""
    result: Set[int] = set()
    if field == '*':
        return set(range(min_val, max_val + 1))
    parts = field.split(',')
    for part in parts:
        if '/' in part:
            range_part, step_part = part.split('/')
            step = int(step_part)
            if range_part == '*':
                start, end = min_val, max_val
            elif '-' in range_part:
                start_str, end_str = range_part.split('-')
                start, end = int(start_str), int(end_str)
            else:
                start = end = int(range_part)
            result.update({v for v in range(start, end + 1) if (v - start) % step == 0})
        elif '-' in part:
            start_str, end_str = part.split('-')
            start, end = int(start_str), int(end_str)
            result.update(range(start, end + 1))
        else:
            result.add(int(part))
    # Clamp to bounds
    return {v for v in result if min_val <= v <= max_val}

def _parse_cron(cron_expr: str):
    minute, hour, dom, month, dow = cron_expr.strip().split()
    minute_set = _expand_field(minute, 0, 59)
    hour_set = _expand_field(hour, 0, 23)
    dom_set = _expand_field(dom, 1, 31)
    month_set = _expand_field(month, 1, 12)
    dow_set = _expand_field(dow, 0, 6)  # Sunday=0
    return minute_set, hour_set, dom_set, month_set, dow_set

def matches(cron_expr: str, dt: datetime.datetime) -> bool:
    minute_set, hour_set, dom_set, month_set, dow_set = _parse_cron(cron_expr)
    return (
        dt.minute in minute_set and
        dt.hour in hour_set and
        dt.day in dom_set and
        dt.month in month_set and
        dt.weekday() in dow_set
    )

def next_fire(cron_expr: str, after_dt: datetime.datetime) -> datetime.datetime:
    minute_set, hour_set, dom_set, month_set, dow_set = _parse_cron(cron_expr)
    # Start checking from the next minute
    candidate = after_dt.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
    while True:
        if (
            candidate.minute in minute_set and
            candidate.hour in hour_set and
            candidate.day in dom_set and
            candidate.month in month_set and
            candidate.weekday() in dow_set
        ):
            return candidate
        candidate += datetime.timedelta(minutes=1)

# Tests
if __name__ == "__main__":
    # R5: */15 * * * * matches minutes 0,15,30,45
    expr1 = "*/15 * * * *"
    for m in [0, 15, 30, 45]:
        dt = datetime.datetime(2023, 1, 1, 12, m)
        assert matches(expr1, dt), f"Expected match at minute {m}"
    for m in [5, 14, 16, 29, 31, 44, 46]:
        dt = datetime.datetime(2023, 1, 1, 12, m)
        assert not matches(expr1, dt), f"Unexpected match at minute {m}"

    # R6: 0 9 * * 1-5 matches 9:00 on weekdays
    expr2 = "0 9 * * 1-5"
    for dow in range(0, 7):
        dt = datetime.datetime(2023, 1, 2 + dow, 9, 0)  # 2023-01-02 is Monday
        expected = dow in range(0, 5)  # Monday(0) to Friday(4) in weekday()
        assert matches(expr2, dt) == expected, f"Weekday {dow} expectation failed"

    # R7: 0 0 1 1 * matches midnight Jan 1st
    expr3 = "0 0 1 1 *"
    dt = datetime.datetime(2023, 1, 1, 0, 0)
    assert matches(expr3, dt)
    dt_wrong = datetime.datetime(2023, 1, 2, 0, 0)
    assert not matches(expr3, dt_wrong)

    # next_fire sanity checks
    after = datetime.datetime(2023, 1, 1, 12, 7)
    nf = next_fire(expr1, after)
    assert nf == datetime.datetime(2023, 1, 1, 12, 15)
    after = datetime.datetime(2023, 1, 1, 8, 59)
    nf = next_fire(expr2, after)
    assert nf == datetime.datetime(2023, 1, 2, 9, 0)  # next Monday
    print("All tests passed.")
