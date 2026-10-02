import heapq
from typing import List, Tuple, Optional

def a_star(grid: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> Tuple[List[Tuple[int, int]], int]:
    rows, cols = len(grid), len(grid[0])
    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < rows and 0 <= c < cols
    def passable(r: int, c: int) -> bool:
        return grid[r][c] != -1
    def neighbors(r: int, c: int):
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r+dr, c+dc
            if in_bounds(nr,nc) and passable(nr,nc):
                yield nr, nc
    def heuristic(a: Tuple[int,int], b: Tuple[int,int]) -> int:
        return abs(a[0]-b[0]) + abs(a[1]-b[1])
    start_r, start_c = start
    goal_r, goal_c = goal
    open_set = []
    heapq.heappush(open_set, (heuristic(start, goal), 0, start))
    g_score = {start: 0}
    came_from = {}
    while open_set:
        _, current_g, current = heapq.heappop(open_set)
        if current == goal:
            break
        for nbr in neighbors(*current):
            tentative_g = g_score[current] + grid[nbr[0]][nbr[1]]
            if nbr not in g_score or tentative_g < g_score[nbr]:
                g_score[nbr] = tentative_g
                f = tentative_g + heuristic(nbr, goal)
                heapq.heappush(open_set, (f, tentative_g, nbr))
                came_from[nbr] = current
    # reconstruct path
    if goal not in came_from and start != goal:
        return [], float('inf')
    path = []
    node = goal
    while node != start:
        path.append(node)
        node = came_from.get(node, start)
    path.append(start)
    path.reverse()
    total_cost = sum(grid[r][c] for r,c in path)
    return path, total_cost

# Example test grid
if __name__ == "__main__":
    test_grid = [
        [1,1,1,1,1,1,1,1,1,1],
        [1,-1,-1,-1,1,1,1,-1,1,1],
        [1,1,1,-1,1,1,1,-1,1,1],
        [1,1,1,-1,1,1,1,-1,1,1],
        [1,1,1,-1,1,1,1,-1,1,1],
        [1,1,1,-1,1,1,1,-1,1,1],
        [1,1,1,-1,1,1,1,-1,1,1],
        [1,1,1,-1,1,1,1,-1,1,1],
        [1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1]
    ]
    start = (0,0)
    goal = (9,9)
    path, cost = a_star(test_grid, start, goal)
    print("Path:", path)
    print("Total cost:", cost)
