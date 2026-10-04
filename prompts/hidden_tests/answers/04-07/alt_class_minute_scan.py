# Correct with a different interface: CronExpression(expr).matches(dt) and
# .next_fire(after), with a plain minute-by-minute search.
import datetime


class CronExpression:
    BOUNDS = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 6))

    def __init__(self, expr):
        self.sets = [self._expand(f, lo, hi) for f, (lo, hi) in zip(expr.split(), self.BOUNDS)]

    @staticmethod
    def _expand(field, lo, hi):
        out = set()
        for item in field.split(","):
            rng, step = (item.split("/") + ["1"])[:2]
            if rng == "*":
                a, b = lo, hi
            elif "-" in rng:
                a, b = (int(x) for x in rng.split("-"))
            else:
                a = b = int(rng)
            out |= set(range(a, b + 1, int(step)))
        return out

    def matches(self, when):
        cron_dow = when.isoweekday() % 7
        return all(v in s for v, s in zip((when.minute, when.hour, when.day, when.month, cron_dow), self.sets))

    def next_fire(self, after):
        t = after.replace(second=0, microsecond=0)
        while True:
            t += datetime.timedelta(minutes=1)
            if self.matches(t):
                return t
