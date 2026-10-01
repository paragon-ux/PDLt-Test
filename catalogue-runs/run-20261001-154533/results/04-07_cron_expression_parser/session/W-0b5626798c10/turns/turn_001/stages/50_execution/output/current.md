import datetime
from typing import List, Set

class CronExpression:
    def __init__(self, expr: str):
        fields = expr.strip().split()
        if len(fields) != 5:
            raise ValueError("Cron expression must have exactly 5 fields")
        self.minute = self._parse_field(fields[0], 0, 59)
        self.hour = self._parse_field(fields[1], 0, 23)
        self.day_of_month = self._parse_field(fields[2], 1, 31)
        self.month = self._parse_field(fields[3], 1, 12)
        self.day_of_week = self._parse_field(fields[4], 0, 6)  # 0=Sunday

    def _parse_field(self, field: str, min_val: int, max_val: int) -> Set[int]:
        result: Set[int] = set()
        parts = field.split(',')
        for part in parts:
            if '/' in part:
                base, step = part.split('/')
                step = int(step)
                if base == '*':
                    start = min_val
                    end = max_val
                elif '-' in base:
                    start_s, end_s = base.split('-')
                    start = int(start_s)
                    end = int(end_s)
                else:
                    start = int(base)
                    end = max_val
                for v in range(start, end + 1):
                    if (v - start) % step == 0:
                        if min_val <= v <= max_val:
                            result.add(v)
            elif '-' in part:
                start_s, end_s = part.split('-')
                start = int(start_s)
                end = int(end_s)
                for v in range(start, end + 1):
                    if min_val <= v <= max_val:
                        result.add(v)
            elif part == '*':
                for v in range(min_val, max_val + 1):
                    result.add(v)
            else:
                v = int(part)
                if min_val <= v <= max_val:
                    result.add(v)
        return result

def matches(cron_expr: str, dt: datetime.datetime) -> bool:
    cron = CronExpression(cron_expr)
    return (
        dt.minute in cron.minute and
        dt.hour in cron.hour and
        dt.day in cron.day_of_month and
        dt.month in cron.month and
        dt.weekday() in cron.day_of_week
    )

def next_fire(cron_expr: str, after_dt: datetime.datetime) -> datetime.datetime:
    cron = CronExpression(cron_expr)
    # start searching from the next minute
    candidate = after_dt.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
    while True:
        if (
            candidate.minute in cron.minute and
            candidate.hour in cron.hour and
            candidate.day in cron.day_of_month and
            candidate.month in cron.month and
            candidate.weekday() in cron.day_of_week
        ):
            return candidate
        candidate += datetime.timedelta(minutes=1)

# Unit tests
if __name__ == "__main__":
    import unittest

    class TestCron(unittest.TestCase):
        def test_quarter_hour(self):
            expr = "*/15 * * * *"
            base = datetime.datetime(2023, 1, 1, 0, 0)
            for minute in [0, 15, 30, 45]:
                dt = base.replace(minute=minute)
                self.assertTrue(matches(expr, dt))
                # ensure next fire advances correctly
                next_dt = next_fire(expr, dt - datetime.timedelta(minutes=1))
                self.assertEqual(next_dt, dt)
            # a minute that should not match
            self.assertFalse(matches(expr, base.replace(minute=22))
        )
        def test_weekday_nine(self):
            expr = "0 9 * * 1-5"
            for day in range(1, 6):  # Monday=0, so 1-5 are Tue-Sat? Adjust accordingly
                dt = datetime.datetime(2023, 1, day+2, 9, 0)  # 2023-01-03 is Tuesday
                self.assertTrue(matches(expr, dt))
                # non-matching hour
                self.assertFalse(matches(expr, dt.replace(hour=8)))
        def test_new_year_midnight(self):
            expr = "0 0 1 1 *"
            dt = datetime.datetime(2023, 1, 1, 0, 0)
            self.assertTrue(matches(expr, dt))
            self.assertFalse(matches(expr, dt + datetime.timedelta(days=1)))
            next_dt = next_fire(expr, datetime.datetime(2022, 12, 31, 23, 59))
            self.assertEqual(next_dt, dt)

    unittest.main()
