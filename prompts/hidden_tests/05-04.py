"""Hidden tests for 05-04: A* on a weighted 4-directional grid.

From the prompt:
- cost -1 is impassable;
- moving into a cell costs its value;
- return the shortest path as (row, col) coordinates plus its total cost.

The call is taken as (grid, start, goal). The result may be (path, cost),
(cost, path) or a dict; "no path" may be None, an empty path, an infinite or -1
cost, or an exception.
"""
TEST_SECONDS = 30


def CANDIDATES():
    return functions_named("a_star", "astar", "a_star_search", "astar_search", "find_path", "shortest_path",
                           "a_star_path", params=3)


def _split(result):
    if isinstance(result, dict):
        path = result.get("path")
        cost = result.get("cost", result.get("total_cost"))
        return path, cost
    if isinstance(result, (tuple, list)) and len(result) == 2:
        a, b = result
        if (a is None or isinstance(a, (list, tuple))) and not isinstance(b, (list, tuple)):
            return a, b
        if (b is None or isinstance(b, (list, tuple))) and not isinstance(a, (list, tuple)):
            return b, a
    raise AssertionError(f"unrecognised result shape: {type(result).__name__}")


def _dijkstra(grid, start, goal):
    import heapq

    rows, cols = len(grid), len(grid[0])
    best = {start: 0}
    heap = [(0, start)]
    while heap:
        d, (r, c) = heapq.heappop(heap)
        if (r, c) == goal:
            return d
        if d > best.get((r, c), float("inf")):
            continue
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] >= 0:
                nd = d + grid[nr][nc]
                if nd < best.get((nr, nc), float("inf")):
                    best[(nr, nc)] = nd
                    heapq.heappush(heap, (nd, (nr, nc)))
    return None


def _grid(seed, size=10, walls=0.2):
    import random

    rng = random.Random(seed)
    grid = [[rng.randint(1, 9) if rng.random() > walls else -1 for _ in range(size)] for _ in range(size)]
    grid[0][0] = grid[size - 1][size - 1] = 1
    return grid


def _check(f, grid, start, goal):
    expected = _dijkstra(grid, start, goal)
    path, cost = _split(f(grid, start, goal))
    path = [tuple(p) for p in path]
    assert path[0] == tuple(start) and path[-1] == tuple(goal), (path[:2], path[-2:])
    walked = 0
    for (r1, c1), (r2, c2) in zip(path, path[1:]):
        assert abs(r1 - r2) + abs(c1 - c2) == 1, "not a 4-directional step"
        assert grid[r2][c2] >= 0, "path enters an impassable cell"
        walked += grid[r2][c2]
    assert walked == expected, (walked, expected)
    assert float(cost) == float(expected), (cost, expected)


def test_optimal_on_random_grids(f):
    for seed in range(8):
        grid = _grid(seed)
        if _dijkstra(grid, (0, 0), (9, 9)) is not None:
            _check(f, grid, (0, 0), (9, 9))


def test_cheap_detour_beats_short_expensive_route(f):
    grid = [[1, 9, 9, 9, 1],
            [1, 9, -1, 9, 1],
            [1, 1, 1, 1, 1]]
    _check(f, grid, (0, 0), (0, 4))


def test_start_equals_goal(f):
    grid = [[1, 2], [3, 4]]
    path, cost = _split(f(grid, (1, 1), (1, 1)))
    assert [tuple(p) for p in path] == [(1, 1)] and float(cost) == 0


def test_unreachable_goal(f):
    grid = [[1, -1, 1], [1, -1, 1], [1, -1, 1]]
    try:
        result = f(grid, (0, 0), (0, 2))
    except Exception:  # noqa: BLE001 - raising is an accepted way to say "no path"
        return
    if result is None:
        return
    path, cost = _split(result)
    assert not path or cost in (None, -1) or cost == float("inf"), (path, cost)


TESTS = [test_optimal_on_random_grids, test_cheap_detour_beats_short_expensive_route, test_start_equals_goal,
         test_unreachable_goal]
