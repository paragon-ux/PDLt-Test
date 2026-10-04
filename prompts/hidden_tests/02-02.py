"""Hidden tests for 02-02: a counting Bloom filter.

From the prompt:
- add(item), remove(item), might_contain(item);
- m and k derived from the expected count n and the false-positive rate p;
- no false negatives;
- a false-positive rate within 2x of the theoretical bound.

The constructor's parameter names are open, so n and p are matched by name,
falling back to position.
"""
TEST_SECONDS = 30
N, P = 1500, 0.01


def CANDIDATES():
    return classes_with("add", "remove", "might_contain")


def _make(C):
    import inspect

    try:
        params = [p for p in inspect.signature(C).parameters.values() if p.name != "self"]
    except (TypeError, ValueError):
        params = []
    kwargs = {}
    for p in params:
        name = p.name.lower()
        if any(t in name for t in ("rate", "prob", "error", "fp", "epsilon")) or name == "p":
            kwargs[p.name] = P
        elif any(t in name for t in ("expected", "capacity", "count", "items", "elements", "size")) or name == "n":
            kwargs[p.name] = N
    if len(kwargs) == 2:
        return C(**kwargs)
    return C(N, P)


def test_no_false_negatives(C):
    f = _make(C)
    items = [f"member-{i}" for i in range(N)]
    for item in items:
        f.add(item)
    assert all(f.might_contain(item) for item in items)


def test_false_positive_rate_within_twice_the_bound(C):
    f = _make(C)
    for i in range(N):
        f.add(f"member-{i}")
    trials = 3000
    false_positives = sum(1 for i in range(trials) if f.might_contain(f"stranger-{i}"))
    assert false_positives / trials <= 2 * P + 0.01, false_positives / trials


def test_remove_keeps_other_members(C):
    f = _make(C)
    members = [f"m{i}" for i in range(600)]
    for item in members:
        f.add(item)
    for item in members[:300]:
        f.remove(item)
    assert all(f.might_contain(item) for item in members[300:]), "a remove caused a false negative"
    still = sum(1 for item in members[:300] if f.might_contain(item))
    assert still / 300 <= 4 * P + 0.02, still


def test_counts_survive_duplicates(C):
    f = _make(C)
    f.add("twice")
    f.add("twice")
    f.remove("twice")
    assert f.might_contain("twice"), "one remove of a twice-added item must keep it"


TESTS = [test_no_false_negatives, test_false_positive_rate_within_twice_the_bound, test_remove_keeps_other_members,
         test_counts_survive_duplicates]
