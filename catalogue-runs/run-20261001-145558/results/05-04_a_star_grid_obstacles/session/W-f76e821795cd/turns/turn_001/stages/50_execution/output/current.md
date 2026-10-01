import heapq
from typing import List, Tuple, Optional

def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Manhattan distance heuristic."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> Tuple[Optional[List[Tuple[int, int]]], Optional[int]]:
    rows, cols = len(grid), len(grid[0])
    open_set = []
    heapq.heappush(open_set, (heuristic(start, goal), 0, start))
    came_from = {}
    g_score = {start: 0}
    closed_set = set()

    while open_set:
        _, current_g, current = heapq.heappop(open_set)
        if current in closed_set:
            continue
        if current == goal:
            # reconstruct path
            path = []
            node = current
            while node != start:
                path.append(node)
                node = came_from[node]
            path.append(start)
            path.reverse()
            return path, g_score[goal]
        closed_set.add(current)
        r, c = current
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if grid[nr][nc] == -1:
                    continue
                neighbor = (nr, nc)
                tentative_g = g_score[current] + grid[nr][nc]
                if neighbor in closed_set:
                    continue
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))
    return None, None

def dijkstra(grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> Tuple[Optional[List[Tuple[int, int]]], Optional[int]]:
    rows, cols = len(grid), len(grid[0])
    pq = []
    heapq.heappush(pq, (0, start))
    came_from = {}
    dist = {start: 0}
    visited = set()
    while pq:
        cur_dist, current = heapq.heappop(pq)
        if current in visited:
            continue
        visited.add(current)
        if current == goal:
            path = []
            node = current
            while node != start:
                path.append(node)
                node = came_from[node]
            path.append(start)
            path.reverse()
            return path, cur_dist
        r, c = current
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if grid[nr][nc] == -1:
                    continue
                neighbor = (nr, nc)
                new_dist = cur_dist + grid[nr][nc]
                if new_dist < dist.get(neighbor, float('inf')):
                    dist[neighbor] = new_dist
                    came_from[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
    return None, None

def test():
    grid = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, -1,-1,-1, 1, 2, 2, 2, 2, 1],
        [1, 1, 1,-1, 1, 2,-1,-1, 2, 1],
        [1,-1, 1,-1, 1, 2, 1, 1, 2, 1],
        [1,-1, 1, 1, 1, 2,-1, 1, 2, 1],
        [1, 1, 1,-1,-1, 2, 1, 1, 2, 1],
        [1,-1, 1, 1, 1, 1, 1,-1, 2, 1],
        [1,-1,-1,-1, 1,-1,-1,-1, 2, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 2, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]
    start = (0, 0)
    goal = (9, 9)
    path_a, cost_a = astar(grid, start, goal)
    path_d, cost_d = dijkstra(grid, start, goal)
    assert path_a is not None and cost_a is not None, "A* failed to find a path"
    assert cost_a == cost_d, f"A* cost {cost_a} differs from Dijkstra cost {cost_d}"
    print("A* path:", path_a)
    print("Total cost:", cost_a)

if __name__ == "__main__":
    test()
