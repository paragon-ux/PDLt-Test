"""Hidden tests for 02-03: a thread-safe sharded LRU cache.

From the prompt:
- N shards (default 16), each with its own lock and capacity;
- hash(key) % N routing;
- independent LRU order per shard;
- get() and put().

The constructor's names are open: shard count and capacity are matched by name.
With a single shard the cache must behave as one LRU of the stated capacity,
whether that capacity is per shard or total.
"""
TEST_SECONDS = 30


def CANDIDATES():
    return classes_with("get", "put")


def _make(C, shards, capacity):
    import inspect

    try:
        params = [p for p in inspect.signature(C).parameters.values() if p.name != "self"]
    except (TypeError, ValueError):
        params = []
    kwargs = {}
    for p in params:
        name = p.name.lower()
        # Capacity words first: "capacity_per_shard" names a capacity, not a shard count.
        if any(t in name for t in ("capacity", "size", "max", "limit")):
            kwargs[p.name] = capacity
        elif "shard" in name or name in ("n", "partitions"):
            kwargs[p.name] = shards
    return C(**kwargs)


def _absent(cache, key):
    try:
        value = cache.get(key)
    except KeyError:
        return True
    return missing(value)


def test_get_put_round_trip(C):
    c = _make(C, 16, 1000)
    for i in range(200):
        c.put(f"k{i}", i)
    assert all(c.get(f"k{i}") == i for i in range(200))
    assert _absent(c, "nope")


def test_single_shard_is_an_lru(C):
    c = _make(C, 1, 3)
    for k in "abc":
        c.put(k, k.upper())
    assert c.get("a") == "A"      # a is now most recent
    c.put("d", "D")               # evicts b, the least recent
    assert _absent(c, "b")
    assert c.get("a") == "A" and c.get("c") == "C" and c.get("d") == "D"


def test_capacity_is_bounded(C):
    c = _make(C, 4, 5)
    for i in range(500):
        c.put(i, i)
    present = sum(1 for i in range(500) if not _absent(c, i))
    assert 0 < present <= 4 * 5, present


def test_concurrent_writers_and_readers(C):
    import threading

    c = _make(C, 16, 4096)
    errors = []

    def worker(tid):
        try:
            for i in range(300):
                key = (tid, i)
                c.put(key, tid * 10_000 + i)
                got = c.get(key)
                if got != tid * 10_000 + i:
                    errors.append((key, got))
        except Exception as exc:  # noqa: BLE001
            errors.append(repr(exc))

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(20)
    assert not errors, errors[:3]
    assert all(c.get((t, i)) == t * 10_000 + i for t in range(8) for i in range(0, 300, 37))


TESTS = [test_get_put_round_trip, test_single_shard_is_an_lru, test_capacity_is_bounded,
         test_concurrent_writers_and_readers]
