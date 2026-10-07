# Wrong: day-of-week uses Python's weekday() (Monday = 0) instead of cron's (Sunday = 0).
from datetime import datetime, timedelta

RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]


def parse_field(spec, lo, hi):
    values = set()
    for part in spec.split(","):
        base, _, step = part.partition("/")
        step = int(step) if step else 1
        if base == "*":
            start, end = lo, hi
        elif "-" in base:
            start, end = map(int, base.split("-"))
        else:
            start = int(base)
            end = hi if step > 1 else start
        if not (lo <= start <= end <= hi) or step < 1:
            raise ValueError(f"bad field {part!r}")
        values.update(range(start, end + 1, step))
    return values


def parse(expr):
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError("a cron expression has 5 fields")
    return [parse_field(p, lo, hi) for p, (lo, hi) in zip(parts, RANGES)]


def matches(cron_expr, dt):
    minute, hour, dom, month, dow = parse(cron_expr)
    return (dt.minute in minute and dt.hour in hour and dt.day in dom and dt.month in month
            and dt.weekday() in dow)


def next_fire(cron_expr, after_datetime):
    minute, hour, dom, month, dow = parse(cron_expr)
    t = after_datetime.replace(second=0, microsecond=0) + timedelta(minutes=1)
    limit = t + timedelta(days=366 * 5)
    while t < limit:
        if t.month not in month:
            t = (t.replace(day=1, hour=0, minute=0) + timedelta(days=32)).replace(day=1)
        elif t.day not in dom or t.weekday() not in dow:
            t = t.replace(hour=0, minute=0) + timedelta(days=1)
        elif t.hour not in hour:
            t = t.replace(minute=0) + timedelta(hours=1)
        elif t.minute not in minute:
            t += timedelta(minutes=1)
        else:
            return t
    raise ValueError("no firing time within five years")
