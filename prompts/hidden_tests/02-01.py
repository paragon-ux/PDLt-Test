"""Hidden tests for 02-01: an O(1) LFU cache with get(key) and put(key, value).

From the prompt:
- evict the least frequently used key when capacity is exceeded;
- among equal frequencies, evict the least recently used;
- get() and put() of an existing key both increment its frequency.

The prompt leaves the "absent" result open, so None, -1 or KeyError all count.
"""
TEST_SECONDS = 15
_ABSENT = object()


def CANDIDATES():
    return classes_with("get", "put")


def _get(cache, key):
    try:
        value = cache.get(key)
    except KeyError:
        return _ABSENT
    return _ABSENT if missing(value) else value


def test_frequency_beats_recency(C):
    c = construct(C, 2)
    c.put(1, 10)
    c.put(2, 20)
    assert _get(c, 1) == 10
    c.put(3, 30)  # key 2 has the lowest frequency
    assert _get(c, 2) is _ABSENT
    assert _get(c, 3) == 30 and _get(c, 1) == 10


def test_least_recent_among_equal_frequency(C):
    c = construct(C, 2)
    c.put(1, 10)
    c.put(2, 20)
    c.put(3, 30)  # 1 and 2 both used once; 1 is older
    assert _get(c, 1) is _ABSENT
    assert _get(c, 2) == 20 and _get(c, 3) == 30


def test_update_increments_frequency(C):
    c = construct(C, 2)
    c.put(1, 10)
    c.put(2, 20)
    c.put(1, 11)  # key 1 now used twice
    c.put(3, 30)
    assert _get(c, 1) == 11 and _get(c, 2) is _ABSENT


def test_reference_sequence(C):
    c = construct(C, 2)
    c.put(1, 1)
    c.put(2, 2)
    assert _get(c, 1) == 1
    c.put(3, 3)
    assert _get(c, 2) is _ABSENT and _get(c, 3) == 3
    c.put(4, 4)
    assert _get(c, 1) is _ABSENT and _get(c, 3) == 3 and _get(c, 4) == 4


def test_random_operations_against_a_model(C):
    import random

    rng = random.Random(7)
    cap = 5
    c = construct(C, cap)
    model, freq, last, clock = {}, {}, {}, 0
    for _ in range(600):
        key = rng.randrange(12)
        clock += 1
        if rng.random() < 0.5:
            got = _get(c, key)
            if key in model:
                freq[key] += 1
                last[key] = clock
                assert got == model[key], (key, got, model[key])
            else:
                assert got is _ABSENT, (key, got)
        else:
            value = rng.randrange(1000, 9999)
            if key in model:
                freq[key] += 1
            else:
                if len(model) >= cap:
                    victim = min(model, key=lambda k: (freq[k], last[k]))
                    del model[victim], freq[victim], last[victim]
                freq[key] = 1
            model[key] = value
            last[key] = clock
            c.put(key, value)


TESTS = [test_frequency_beats_recency, test_least_recent_among_equal_frequency, test_update_increments_frequency,
         test_reference_sequence, test_random_operations_against_a_model]
