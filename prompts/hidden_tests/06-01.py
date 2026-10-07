"""Hidden tests for 06-01: the fixed binary search.

The deliverable may keep the original next to the fix under another name, so
every two-argument function whose name mentions a binary search is a candidate,
names that say "fixed" (or similar) first. A candidate passes if it finds every
present target (any index holding it, for duplicates), reports a missing one as
-1 or None, and always terminates.
"""
TEST_SECONDS = 15
_PREFER = ("fix", "correct", "safe", "new", "good")


def CANDIDATES():
    import inspect

    found = []
    for f in functions_named("binary_search", params=2):
        name = f.__name__.lower()
        if "search" not in name and "bsearch" not in name:
            continue
        try:
            required = [p for p in inspect.signature(f).parameters.values() if p.default is p.empty]
        except (TypeError, ValueError):
            continue
        if len(required) == 2:
            found.append(f)
    return sorted(found, key=lambda f: (not any(p in f.__name__.lower() for p in _PREFER), f.__name__))


def _check(f, arr, target):
    got = f(list(arr), target)
    if target in arr:
        assert isinstance(got, int) and not isinstance(got, bool) and 0 <= got < len(arr) and arr[got] == target, \
            (arr, target, got)
    else:
        assert missing(got), (arr, target, got)


def test_prompt_example(f):
    arr = [1, 3, 5, 7, 9, 11, 13]
    for target in [1, 7, 13, 4, 0, 14]:
        _check(f, arr, target)


def test_every_position_and_gap(f):
    for n in range(0, 12):
        arr = list(range(1, 2 * n + 1, 2))
        for target in range(0, 2 * n + 2):
            _check(f, arr, target)


def test_random_arrays(f):
    import random

    rng = random.Random(5)
    for _ in range(300):
        arr = sorted(rng.sample(range(-50, 50), rng.randint(0, 25)))
        _check(f, arr, rng.randint(-55, 55))
    for _ in range(100):
        arr = sorted(rng.choice(range(5)) for _ in range(rng.randint(1, 15)))
        _check(f, arr, rng.randint(-1, 5))


TESTS = [test_prompt_example, test_every_position_and_gap, test_random_arrays]
