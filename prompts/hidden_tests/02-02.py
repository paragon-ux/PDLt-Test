"""Hidden tests for 02-02: a skip-list ordered map.

From the prompt:
- insert(key, value) inserts or updates;
- search(key) returns the value, or None;
- delete(key) removes the key;
- range_query(lo, hi) returns all key-value pairs with lo <= key <= hi.

A list of pairs is checked for ascending order; a dict is accepted too.
"""
TEST_SECONDS = 15


def CANDIDATES():
    return classes_with("insert", "search", "delete", "range_query")


def _pairs(result):
    if isinstance(result, dict):
        return sorted(result.items())
    pairs = [tuple(p) for p in result]
    assert all(len(p) == 2 for p in pairs), pairs[:3]
    assert [k for k, _ in pairs] == sorted(k for k, _ in pairs), "range_query must be in key order"
    return pairs


def test_insert_search_update(C):
    s = construct(C)
    for k in [5, 1, 9, 3, 7]:
        s.insert(k, f"v{k}")
    assert s.search(3) == "v3" and s.search(9) == "v9"
    assert s.search(4) is None
    s.insert(3, "new")
    assert s.search(3) == "new"


def test_delete(C):
    s = construct(C)
    for k in range(20):
        s.insert(k, k * k)
    for k in range(0, 20, 2):
        s.delete(k)
    assert all(s.search(k) is None for k in range(0, 20, 2))
    assert all(s.search(k) == k * k for k in range(1, 20, 2))


def test_range_query_inclusive(C):
    s = construct(C)
    for k in range(0, 100, 5):
        s.insert(k, -k)
    assert _pairs(s.range_query(10, 30)) == [(10, -10), (15, -15), (20, -20), (25, -25), (30, -30)]
    assert _pairs(s.range_query(31, 34)) == []
    assert _pairs(s.range_query(-5, 4)) == [(0, 0)]


def test_random_against_a_dict(C):
    import random

    rng = random.Random(11)
    s, model = construct(C), {}
    for _ in range(1500):
        op, key = rng.random(), rng.randrange(300)
        if op < 0.5:
            s.insert(key, key + 1)
            model[key] = key + 1
        elif op < 0.7:
            s.delete(key)
            model.pop(key, None)
        else:
            assert s.search(key) == model.get(key)
    lo, hi = 50, 200
    assert _pairs(s.range_query(lo, hi)) == sorted((k, v) for k, v in model.items() if lo <= k <= hi)


TESTS = [test_insert_search_update, test_delete, test_range_query_inclusive, test_random_against_a_dict]
