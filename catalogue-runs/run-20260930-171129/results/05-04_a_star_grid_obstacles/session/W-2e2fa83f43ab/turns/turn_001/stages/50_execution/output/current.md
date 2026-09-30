# A* pathfinding implementation with verification against Dijkstra
import heapq
from typing import List, Tuple, Optional

def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Manhattan distance heuristic."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def neighbors(pos: Tuple[int, int], grid: List[List[int]]) -> List[Tuple[int, int]]:
    rows, cols = len(grid), len(grid[0])
    r, c = pos
    result = []
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != -1:
            result.append((nr, nc))
    return result

def reconstruct_path(came_from: dict, current: Tuple[int, int]) -> List[Tuple[int, int]]:
    total_path = [current]
    while current in came_from:
        current = came_from[current]
        total_path.append(current)
    total_path.reverse()
    return total_path

def a_star(grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> Tuple[Optional[List[Tuple[int, int]]], Optional[int]]:
    open_set = []
    heapq.heappush(open_set, (0 + heuristic(start, goal), 0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    while open_set:
        _, current_g, current = heapq.heappop(open_set)
        if current == goal:
            path = reconstruct_path(came_from, current)
            total_cost = sum(grid[r][c] for r, c in path[1:])  # cost excludes start cell
            return path, total_cost
        for neighbor in neighbors(current, grid):
            tentative_g = g_score[current] + grid[neighbor[0]][neighbor[1]]
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristic(neighbor, goal)
                f_score[neighbor] = f
                heapq.heappush(open_set, (f, tentative_g, neighbor))
    return None, None

def dijkstra(grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> Tuple[Optional[List[Tuple[int, int]]], Optional[int]]:
    rows, cols = len(grid), len(grid[0])
    dist = {start: 0}
    prev = {}
    heap = [(0, start)]
    while heap:
        d, node = heapq.heappop(heap)
        if node == goal:
            break
        for nb in neighbors(node, grid):
            nd = d + grid[nb[0]][nb[1]]
            if nb not in dist or nd < dist[nb]:
                dist[nb] = nd
                prev[nb] = node
                heapq.heappush(heap, (nd, nb))
    if goal not in dist:
        return None, None
    # reconstruct
    path = []
    cur = goal
    while cur != start:
        path.append(cur)
        cur = prev[cur]
    path.append(start)
    path.reverse()
    return path, dist[goal]

def test():
    grid = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, -1,-1,-1, 1, 2, 2, 2, 2, 1],
        [1, 1, 1,-1, 1, 2,-1,-1,-1, 1],
        [1, 2, 1,-1, 1, 2, 1, 1, 1, 1],
        [1, 2, 1, 1, 1, 2, 1,-1, 1, 1],
        [1, 2,-1,-1,-1, 2, 1,-1, 1, 1],
        [1, 2, 1, 1, 1, 2, 1, 1, 1, 1],
        [1, 2, 1,-1, 1, 2, 2, 2, 2, 1],
        [1, 2, 1,-1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]
    start = (0,0)
    goal = (9,9)
    path_a, cost_a = a_star(grid, start, goal)
    path_d, cost_d = dijkstra(grid, start, goal)
    print("A* path:", path_a)
    print("A* cost:", cost_a)
    print("Dijkstra cost:", cost_d)
    assert cost_a == cost_d, "A* cost does not match Dijkstra optimal cost"
    print("Verification passed: A* cost matches Dijkstra optimal cost.")

if __name__ == "__main__":
    test()
