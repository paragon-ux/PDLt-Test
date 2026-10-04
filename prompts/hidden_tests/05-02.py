"""Hidden tests for 05-02: a gift-wrapping convex hull, counter-clockwise, with
every point on the hull boundary included.

From the prompt:
- the input is a list of (x, y) tuples;
- the output is the hull in counter-clockwise order;
- collinear boundary points are included;
- the cases are collinear edges, all points collinear, and duplicates.

Any rotation of the expected cycle is accepted. For all points collinear, the
boundary is the segment itself, so every distinct point must be present, in any
order.
"""
TEST_SECONDS = 20


def CANDIDATES():
    return functions_named("convex_hull", "gift_wrap", "gift_wrapping", "jarvis_march", "jarvis",
                           "gift_wrapping_hull", "hull", params=1)


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _reference(points):
    pts = sorted(set(map(tuple, points)))
    if len(pts) <= 2:
        return pts
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) < 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) < 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _same_cycle(got, expected):
    if len(got) != len(expected):
        return False
    if not expected:
        return True
    try:
        start = got.index(expected[0])
    except ValueError:
        return False
    return got[start:] + got[:start] == expected


def _hull(f, points):
    return [tuple(p) for p in f(list(points))]


def test_square_with_interior_points(f):
    pts = [(0, 0), (4, 0), (4, 4), (0, 4), (1, 1), (2, 3), (3, 2)]
    assert _same_cycle(_hull(f, pts), _reference(pts))


def test_collinear_edge_points_included(f):
    pts = [(0, 0), (2, 0), (4, 0), (4, 2), (4, 4), (2, 4), (0, 4), (0, 2), (2, 2), (1, 3)]
    assert _same_cycle(_hull(f, pts), _reference(pts))


def test_random_points(f):
    import random

    rng = random.Random(9)
    for _ in range(5):
        pts = [(rng.randint(-20, 20), rng.randint(-20, 20)) for _ in range(40)]
        assert _same_cycle(_hull(f, pts), _reference(pts)), "hull differs on a random set"


def test_all_collinear(f):
    pts = [(0, 0), (1, 1), (2, 2), (3, 3), (5, 5)]
    assert set(_hull(f, pts)) == set(pts)


def test_duplicates_appear_once(f):
    pts = [(0, 0), (0, 0), (3, 0), (3, 0), (3, 3), (0, 3), (0, 3), (1, 1)]
    got = _hull(f, pts)
    assert len(got) == len(set(got)), "a duplicate point appears twice"
    assert _same_cycle(got, _reference(pts))


TESTS = [test_square_with_interior_points, test_collinear_edge_points_included, test_random_points,
         test_all_collinear, test_duplicates_appear_once]
