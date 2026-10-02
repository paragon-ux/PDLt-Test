import datetime
from typing import List, Set

# Helper functions to parse each cron field

def parse_field(field: str, min_val: int, max_val: int) -> Set[int]:
    """Parse a single cron field into a set of allowed integer values.
    Supports '*', single numbers, ranges, steps, and comma lists.
    """
    result: Set[int] = set()
    if field == '*':
        return set(range(min_val, max_val + 1))
    for part in field.split(','):
        if '/' in part:
            base, step_str = part.split('/')
            step = int(step_str)
            if base == '*':
                start, end = min_val, max_val
            elif '-' in base:
                start_str, end_str = base.split('-')
                start, end = int(start_str), int(end_str)
            else:
                start = int(base)
                end = max_val
            for v in range(start, end + 1, step):
                if min_val <= v <= max_val:
                    result.add(v)
        elif '-' in part:
            start_str, end_str = part.split('-')
            start, end = int(start_str), int(end_str)
            for v in range(start, end + 1):
                if min_val <= v <= max_val:
                    result.add(v)
        else:
            v = int(part)
            if min_val <= v <= max_val:
                result.add(v)
    return result


def parse_cron(cron_expr: str) -> List[Set[int]]:
    """Parse a full cron expression into a list of allowed values for each field.
    Returns a list of five sets: minute, hour, day-of-month, month, day-of-week.
    """
    fields = cron_expr.strip().split()
    if len(fields) != 5:
        raise ValueError('Cron expression must have exactly 5 fields')
    minute = parse_field(fields[0], 0, 59)
    hour = parse_field(fields[1], 0, 23)
    dom = parse_field(fields[2], 1, 31)
    month = parse_field(fields[3], 1, 12)
    dow = parse_field(fields[4], 0, 6)  # Sunday=0
    return [minute, hour, dom, month, dow]


def matches(cron_expr: str, dt: datetime.datetime) -> bool:
    """Return True if the given datetime matches the cron expression."""
    minute_set, hour_set, dom_set, month_set, dow_set = parse_cron(cron_expr)
    return (
        dt.minute in minute_set and
        dt.hour in hour_set and
        dt.day in dom_set and
        dt.month in month_set and
        dt.weekday() % 7 in dow_set
    )


def next_fire(cron_expr: str, after_dt: datetime.datetime) -> datetime.datetime:
    """Find the next datetime after `after_dt` that matches the cron expression.
    The search is inclusive of the second after `after_dt` (i.e., it will not
    return `after_dt` itself even if it matches)."""
    minute_set, hour_set, dom_set, month_set, dow_set = parse_cron(cron_expr)
    # Start searching from the next minute
    candidate = after_dt.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
    while True:
        if (
            candidate.minute in minute_set and
            candidate.hour in hour_set and
            candidate.day in dom_set and
            candidate.month in month_set and
            candidate.weekday() % 7 in dow_set
        ):
            return candidate
        candidate += datetime.timedelta(minutes=1)

# Unit tests
if __name__ == "__main__":
    import unittest

    class CronTest(unittest.TestCase):
        def test_quarter_hour(self):
            expr = "*/15 * * * *"
            for minute in [0, 15, 30, 45]:
                dt = datetime.datetime(2023, 1, 1, 12, minute)
                self.assertTrue(matches(expr, dt))
            for minute in [5, 10, 20, 35, 50]:
                dt = datetime.datetime(2023, 1, 1, 12, minute)
                self.assertFalse(matches(expr, dt))
            # next_fire checks
            start = datetime.datetime(2023, 1, 1, 12, 7)
            next_dt = next_fire(expr, start)
            self.assertEqual(next_dt, datetime.datetime(2023, 1, 1, 12, 15))

        def test_weekday_9am(self):
            expr = "0 9 * * 1-5"
            # Monday
            dt = datetime.datetime(2023, 1, 2, 9, 0)
            self.assertTrue(matches(expr, dt))
            # Saturday should be false
            dt_sat = datetime.datetime(2023, 1, 7, 9, 0)
            self.assertFalse(matches(expr, dt_sat))
            # next_fire from Friday 8:00 -> Friday 9:00
            start = datetime.datetime(2023, 1, 6, 8, 0)
            next_dt = next_fire(expr, start)
            self.assertEqual(next_dt, datetime.datetime(2023, 1, 6, 9, 0))
            # next_fire from Friday 9:01 -> Monday 9:00
            start = datetime.datetime(2023, 1, 6, 9, 1)
            next_dt = next_fire(expr, start)
            self.assertEqual(next_dt, datetime.datetime(2023, 1, 9, 9, 0))

        def test_jan_first_midnight(self):
            expr = "0 0 1 1 *"
            dt = datetime.datetime(2024, 1, 1, 0, 0)
            self.assertTrue(matches(expr, dt))
            # Different month/day should be false
            dt2 = datetime.datetime(2024, 2, 1, 0, 0)
            self.assertFalse(matches(expr, dt2))
            # next_fire after Dec 31, 2023 23:59 -> Jan 1, 2024 00:00
            start = datetime.datetime(2023, 12, 31, 23, 59)
            next_dt = next_fire(expr, start)
            self.assertEqual(next_dt, datetime.datetime(2024, 1, 1, 0, 0))

    unittest.main(argv=['first-arg-is-ignored'], exit=False)
