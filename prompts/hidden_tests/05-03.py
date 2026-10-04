"""Hidden tests for 05-03: insert an interval into sorted non-overlapping intervals and merge.

From the prompt:
- the example: [[1,3],[6,9],[12,15],[18,20]] + [5,13] -> [[1,3],[5,15],[18,20]];
- insertion at the beginning, end and middle;
- an interval that merges everything; one that overlaps nothing;
- an empty list.

No test uses intervals that only touch at an endpoint, which the prompt leaves
open.
"""
TEST_SECONDS = 15


def CANDIDATES():
    return functions_named("insert", "insert_interval", "merge_insert", "insert_and_merge", "insert_intervals",
                           params=2)


def _norm(result):
    return [tuple(i) for i in result]


def _reference(intervals, new):
    out, (lo, hi) = [], new
    placed = False
    for a, b in intervals:
        if b < lo:
            out.append((a, b))
        elif a > hi:
            if not placed:
                out.append((lo, hi))
                placed = True
            out.append((a, b))
        else:
            lo, hi = min(lo, a), max(hi, b)
    if not placed:
        out.append((lo, hi))
    return out


def test_prompt_example(f):
    assert _norm(f([[1, 3], [6, 9], [12, 15], [18, 20]], [5, 13])) == [(1, 3), (5, 15), (18, 20)]


def test_positions(f):
    base = [[3, 5], [8, 10], [14, 16]]
    assert _norm(f([list(i) for i in base], [0, 1])) == [(0, 1), (3, 5), (8, 10), (14, 16)]
    assert _norm(f([list(i) for i in base], [20, 22])) == [(3, 5), (8, 10), (14, 16), (20, 22)]
    assert _norm(f([list(i) for i in base], [11, 12])) == [(3, 5), (8, 10), (11, 12), (14, 16)]


def test_merges_all_and_empty(f):
    assert _norm(f([[2, 4], [6, 8], [10, 12]], [1, 13])) == [(1, 13)]
    assert _norm(f([], [4, 7])) == [(4, 7)]
    assert _norm(f([[1, 2], [7, 9]], [3, 5])) == [(1, 2), (3, 5), (7, 9)]


def test_random_against_reference(f):
    import random

    rng = random.Random(4)
    for _ in range(200):
        points = sorted(rng.sample(range(0, 200, 2), 8))
        intervals = [[points[i], points[i + 1] - 1 if points[i + 1] - 1 > points[i] else points[i]]
                     for i in range(0, 8, 2)]
        lo = rng.randrange(-5, 205) * 2 + 1
        new = [lo, lo + rng.randrange(1, 40) * 2]
        assert _norm(f([list(i) for i in intervals], list(new))) == _reference([tuple(i) for i in intervals], new)


TESTS = [test_prompt_example, test_positions, test_merges_all_and_empty, test_random_against_reference]
