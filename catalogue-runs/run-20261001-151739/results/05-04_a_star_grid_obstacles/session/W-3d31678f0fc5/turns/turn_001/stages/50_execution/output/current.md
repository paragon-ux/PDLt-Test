import heapq
from typing import List, Tuple, Optional

def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> Tuple[List[Tuple[int, int]], Optional[int]]:
    rows, cols = len(grid), len(grid[0])
    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < rows and 0 <= c < cols
    def passable(r: int, c: int) -> bool:
        return grid[r][c] != -1
    open_set = []
    heapq.heappush(open_set, (manhattan(start, goal), 0, start))  # (f, g, cell)
    g_score = {start: 0}
    came_from = {}
    while open_set:
        _, current_g, current = heapq.heappop(open_set)
        if current == goal:
            # reconstruct path
            path = []
            node = goal
            while node != start:
                path.append(node)
                node = came_from[node]
            path.append(start)
            path.reverse()
            return path, g_score[goal]
        r, c = current
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            nr, nc = r+dr, c+dc
            if not in_bounds(nr, nc) or not passable(nr, nc):
                continue
            tentative_g = current_g + grid[nr][nc]
            neighbor = (nr, nc)
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                f = tentative_g + manhattan(neighbor, goal)
                heapq.heappush(open_set, (f, tentative_g, neighbor))
                came_from[neighbor] = current
    return [], None

def dijkstra(grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> Tuple[List[Tuple[int, int]], Optional[int]]:
    rows, cols = len(grid), len(grid[0])
    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < rows and 0 <= c < cols
    def passable(r: int, c: int) -> bool:
        return grid[r][c] != -1
    open_set = []
    heapq.heappush(open_set, (0, start))  # (g, cell)
    g_score = {start: 0}
    came_from = {}
    while open_set:
        current_g, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            node = goal
            while node != start:
                path.append(node)
                node = came_from[node]
            path.append(start)
            path.reverse()
            return path, g_score[goal]
        r, c = current
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            nr, nc = r+dr, c+dc
            if not in_bounds(nr, nc) or not passable(nr, nc):
                continue
            tentative_g = current_g + grid[nr][nc]
            neighbor = (nr, nc)
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                heapq.heappush(open_set, (tentative_g, neighbor))
                came_from[neighbor] = current
    return [], None

def test():
    grid = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, -1, -1, -1, 1, 2, 2, 2, -1, 1],
        [1, 1, 1, -1, 1, 2, -1, 1, -1, 1],
        [1, -1, 1, -1, 1, 2, -1, 1, 1, 1],
        [1, -1, 1, 1, 1, 2, -1, -1, -1, 1],
        [1, 1, 1, -1, -1, 2, 2, 2, 1, 1],
        [1, -1, 1, 1, 1, 1, -1, 1, 1, 1],
        [1, -1, -1, -1, -1, 1, -1, -1, -1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]
    start = (0, 0)
    goal = (9, 9)
    path_a, cost_a = astar(grid, start, goal)
    path_d, cost_d = dijkstra(grid, start, goal)
    print("A* path cost:", cost_a)
    print("Dijkstra path cost:", cost_d)
    print("Paths equal?", cost_a == cost_d)
    print("A* path length:", len(path_a))
    print("Dijkstra path length:", len(path_d))

if __name__ == "__main__":
    test()
