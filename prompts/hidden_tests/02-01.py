"""Hidden tests for 02-01: a B+ tree with insert, search, range_scan and byte serialization.

The prompt names:
- insert(key, value), search(key), range_scan(lo, hi);
- serializing "the entire tree to bytes" and deserializing it back.

What the prompt leaves open, and how it is handled:
- **range_scan:** its result shape (pairs, values or keys) and the inclusivity of
  its bounds. The bounds tested are absent keys, so inclusivity cannot matter.
- **Serialization:** it may be a method, a classmethod or module functions;
  every route is tried.
"""
TEST_SECONDS = 20


def CANDIDATES():
    return classes_with("insert", "search", "range_scan")


def _tree(C):
    return construct(C, 4)


def _absent(tree, key):
    try:
        return tree.search(key) is None
    except KeyError:
        return True


def _scan_keys(result, values_to_keys):
    items = list(result)
    if items and isinstance(items[0], (tuple, list)) and len(items[0]) == 2:
        return [k for k, _ in items]
    return [values_to_keys.get(v, v) for v in items]


def test_insert_and_search_with_splits(C):
    import random

    t = _tree(C)
    keys = list(range(0, 600, 3))
    random.Random(5).shuffle(keys)
    for k in keys:
        t.insert(k, f"v{k}")
    assert all(t.search(k) == f"v{k}" for k in keys)
    assert _absent(t, 1) and _absent(t, 10_000)


def test_range_scan_in_order(C):
    t = _tree(C)
    for k in range(0, 300, 2):
        t.insert(k, f"v{k}")
    to_keys = {f"v{k}": k for k in range(0, 300, 2)}
    assert _scan_keys(t.range_scan(51, 99), to_keys) == list(range(52, 99, 2))
    assert _scan_keys(t.range_scan(301, 400), to_keys) == []


def _serialize(t):
    for name in ("serialize", "to_bytes", "dumps", "dump"):
        fn = getattr(t, name, None)
        if callable(fn):
            return fn()
    fn = NS.get("serialize")
    if callable(fn):
        return fn(t)
    raise AssertionError("no serialize operation found")


def _deserialize(C, data):
    for name in ("deserialize", "from_bytes", "loads", "load"):
        fn = getattr(C, name, None)
        if callable(fn):
            try:
                result = fn(data)
            except TypeError:
                result = None
            if result is not None:
                return result
            instance = _tree(C)
            got = getattr(instance, name)(data)
            return got if got is not None else instance
    fn = NS.get("deserialize")
    if callable(fn):
        return fn(data)
    raise AssertionError("no deserialize operation found")


def test_serialize_round_trip(C):
    t = _tree(C)
    for k in range(200):
        t.insert(k * 7 % 211, k)
    data = _serialize(t)
    assert isinstance(data, (bytes, bytearray)), type(data)
    restored = _deserialize(C, bytes(data))
    assert all(restored.search(k * 7 % 211) == k for k in range(200))
    to_keys = {k: k * 7 % 211 for k in range(200)}
    original = _scan_keys(t.range_scan(-1, 1000), to_keys)
    assert _scan_keys(restored.range_scan(-1, 1000), to_keys) == original == sorted(original)


TESTS = [test_insert_and_search_with_splits, test_range_scan_in_order, test_serialize_round_trip]
