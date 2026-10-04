"""Hidden tests for 04-07: a 5-field cron parser with matches() and next_fire().

From the prompt:
- fields minute, hour, day-of-month, month, day-of-week;
- values, ranges, steps (*/15, 1-30/5), lists and *;
- matches(cron_expr, datetime) -> bool;
- next_fire(cron_expr, after_datetime) -> datetime.

Expected answers come from a direct reading of standard cron:
- day-of-week 0 is Sunday;
- a step over * starts at the field's minimum.

Two things standard cron leaves to the implementation are not tested:
- restricting day-of-month and day-of-week together (cron ORs them; many
  implementations AND them);
- next_fire from an instant that itself matches.

next_fire is checked from instants with non-zero seconds, so "after" is
unambiguous, and only where the next firing is at most two days away: the prompt
asks for correctness, not speed, so a minute-by-minute search must not run out
of the sandbox's step budget.

The functions may also be methods of a class built from the expression
(Cron(expr).matches(dt), Cron(expr).next_fire(dt)).
"""
TEST_SECONDS = 40
_MATCH = ("matches", "match", "cron_matches", "is_match")
_NEXT = ("next_fire", "next_fire_time", "next_run", "get_next", "next_match", "next_time", "next")


class _Pair:
    def __init__(self, name, matches, next_fire):
        self.__name__, self.matches, self.next_fire = name, matches, next_fire


def CANDIDATES():
    found = []
    m = functions_named(*_MATCH, params=2)
    n = functions_named(*_NEXT, params=2)
    if m and n:
        found.append(_Pair(f"{m[0].__name__}/{n[0].__name__}", m[0], n[0]))
    for cls in classes_with():
        mm = next((x for x in _MATCH if callable(getattr(cls, x, None))), None)
        nn = next((x for x in _NEXT if callable(getattr(cls, x, None))), None)
        if mm and nn:
            found.append(_Pair(f"{cls.__name__}.{mm}/{nn}", _bound(cls, mm), _bound(cls, nn)))
    return found


def _bound(cls, method):
    def call(expr, dt):
        try:
            return getattr(cls(expr), method)(dt)
        except TypeError:
            return getattr(cls(), method)(expr, dt)

    return call


_RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]


def _field(spec, lo, hi):
    values = set()
    for part in spec.split(","):
        step = 1
        if "/" in part:
            part, step = part.split("/")
            step = int(step)
        if part == "*":
            a, b = lo, hi
        elif "-" in part:
            a, b = map(int, part.split("-"))
        else:
            a = b = int(part)
            if step != 1:
                b = hi
        values.update(range(a, b + 1, step))
    return values


def _oracle_matches(expr, dt):
    fields = [_field(s, lo, hi) for s, (lo, hi) in zip(expr.split(), _RANGES)]
    dow = (dt.weekday() + 1) % 7
    return dt.minute in fields[0] and dt.hour in fields[1] and dt.day in fields[2] and \
        dt.month in fields[3] and dow in fields[4]


def _oracle_next(expr, after):
    import datetime as _dt

    t = after.replace(second=0, microsecond=0) + _dt.timedelta(minutes=1)
    fields = [_field(s, lo, hi) for s, (lo, hi) in zip(expr.split(), _RANGES)]
    while True:
        if t.month not in fields[3]:
            t = (t.replace(day=1, hour=0, minute=0) + _dt.timedelta(days=32)).replace(day=1)
            continue
        if t.day not in fields[2] or (t.weekday() + 1) % 7 not in fields[4]:
            t = t.replace(hour=0, minute=0) + _dt.timedelta(days=1)
            continue
        if t.hour not in fields[1]:
            t = t.replace(minute=0) + _dt.timedelta(hours=1)
            continue
        if t.minute not in fields[0]:
            t += _dt.timedelta(minutes=1)
            continue
        return t


def _same(a, b):
    return (a.year, a.month, a.day, a.hour, a.minute, a.second) == (b.year, b.month, b.day, b.hour, b.minute, b.second)


def test_prompt_examples(c):
    from datetime import datetime as D

    for minute in range(60):
        assert bool(c.matches("*/15 * * * *", D(2026, 5, 4, 10, minute))) is (minute % 15 == 0), minute
    assert c.matches("0 9 * * 1-5", D(2026, 10, 5, 9, 0))          # Monday
    assert c.matches("0 9 * * 1-5", D(2026, 10, 9, 9, 0))          # Friday
    assert not c.matches("0 9 * * 1-5", D(2026, 10, 10, 9, 0))     # Saturday
    assert not c.matches("0 9 * * 1-5", D(2026, 10, 4, 9, 0))      # Sunday
    assert not c.matches("0 9 * * 1-5", D(2026, 10, 5, 10, 0))
    assert c.matches("0 0 1 1 *", D(2027, 1, 1, 0, 0))
    assert not c.matches("0 0 1 1 *", D(2027, 1, 2, 0, 0))
    assert _same(c.next_fire("*/15 * * * *", D(2026, 5, 4, 10, 7, 30)), D(2026, 5, 4, 10, 15))
    assert _same(c.next_fire("0 9 * * 1-5", D(2026, 10, 9, 9, 0, 30)), D(2026, 10, 12, 9, 0))
    assert _same(c.next_fire("0 0 1 1 *", D(2026, 12, 31, 23, 10, 1)), D(2027, 1, 1, 0, 0))


def test_field_syntax(c):
    from datetime import datetime as D

    assert c.matches("1-30/5 * * * *", D(2026, 1, 1, 0, 26)) and not c.matches("1-30/5 * * * *", D(2026, 1, 1, 0, 30))
    assert c.matches("5 1,3,5 * * *", D(2026, 1, 1, 3, 5)) and not c.matches("5 1,3,5 * * *", D(2026, 1, 1, 2, 5))
    assert c.matches("* * */2 * *", D(2026, 1, 3, 0, 0)) and not c.matches("* * */2 * *", D(2026, 1, 4, 0, 0))
    assert c.matches("0 0 * */3 *", D(2026, 7, 1, 0, 0)) and not c.matches("0 0 * */3 *", D(2026, 8, 1, 0, 0))
    assert c.matches("0 0 * * 0", D(2026, 10, 4, 0, 0)) and not c.matches("0 0 * * 0", D(2026, 10, 3, 0, 0))
    assert c.matches("10-20,40 * * * *", D(2026, 1, 1, 0, 40)) and not c.matches("10-20,40 * * * *", D(2026, 1, 1, 0, 21))


def test_random_against_reference(c):
    import random
    from datetime import datetime as D, timedelta

    rng = random.Random(3)

    def spec(lo, hi, star_ok=True):
        r = rng.random()
        if r < 0.3 and star_ok:
            return "*"
        if r < 0.45:
            return f"*/{rng.randint(2, max(2, (hi - lo) // 2))}"
        a = rng.randint(lo, hi)
        if r < 0.65:
            return str(a)
        b = rng.randint(a, hi)
        if r < 0.85:
            return f"{a}-{b}" + (f"/{rng.randint(2, 4)}" if rng.random() < 0.4 else "")
        return ",".join(sorted({str(rng.randint(lo, hi)) for _ in range(3)}, key=int))

    for _ in range(40):
        dom_restricted = rng.random() < 0.5
        expr = " ".join([spec(0, 59), spec(0, 23), spec(1, 28) if dom_restricted else "*", spec(1, 12),
                         "*" if dom_restricted else spec(0, 6)])
        start = D(2026, 1, 1) + timedelta(minutes=rng.randint(0, 525000), seconds=rng.randint(1, 59))
        for k in range(5):
            dt = (start + timedelta(minutes=97 * k)).replace(second=0)
            assert bool(c.matches(expr, dt)) is _oracle_matches(expr, dt), (expr, dt)
        expected = _oracle_next(expr, start)
        if expected - start <= timedelta(days=2):
            got = c.next_fire(expr, start)
            assert _same(got, expected), (expr, start, got)


TESTS = [test_prompt_examples, test_field_syntax, test_random_against_reference]
