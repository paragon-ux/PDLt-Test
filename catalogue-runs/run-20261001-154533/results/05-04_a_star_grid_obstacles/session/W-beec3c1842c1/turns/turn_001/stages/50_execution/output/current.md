import heapq

def a_star_pathfinding(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    def neighbors(r, c):
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != -1:
                yield nr, nc
    open_set = []
    heapq.heappush(open_set, (heuristic(start, goal), 0, start, [start]))
    g_score = {start: 0}
    while open_set:
        _, cur_cost, current, path = heapq.heappop(open_set)
        if current == goal:
            return path, cur_cost
        for nb in neighbors(*current):
            tentative_g = cur_cost + grid[nb[0]][nb[1]]
            if nb not in g_score or tentative_g < g_score[nb]:
                g_score[nb] = tentative_g
                f = tentative_g + heuristic(nb, goal)
                heapq.heappush(open_set, (f, tentative_g, nb, path + [nb]))
    return None, float('inf')

def dijkstra_path_cost(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    def neighbors(r, c):
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != -1:
                yield nr, nc
    dist = {start: 0}
    heap = [(0, start)]
    while heap:
        d, current = heapq.heappop(heap)
        if current == goal:
            return d
        if d > dist[current]:
            continue
        for nb in neighbors(*current):
            nd = d + grid[nb[0]][nb[1]]
            if nb not in dist or nd < dist[nb]:
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))
    return float('inf')

def create_grid():
    # 10x10 grid with varied costs and some walls (-1)
    grid = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, -1, -1, -1, 1, 2, 2, 2, -1, 1],
        [1, 2, 3, -1, 1, 3, -1, 2, -1, 1],
        [1, 2, 3, 1, 1, 3, 1, 2, 1, 1],
        [1, -1, -1, -1, 1, -1, -1, -1, -1, 1],
        [1, 1, 1, 1, 1, 2, 2, 2, 2, 1],
        [1, 2, -1, -1, -1, -1, -1, -1, 2, 1],
        [1, 2, 2, 2, 2, 2, 2, -1, 2, 1],
        [1, -1, -1, -1, -1, -1, 2, -1, -1, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ]
    return grid

def main():
    grid = create_grid()
    start = (0, 0)
    goal = (9, 9)
    path, cost = a_star_pathfinding(grid, start, goal)
    optimal_cost = dijkstra_path_cost(grid, start, goal)
    print("A* path:", path)
    print("A* total cost:", cost)
    print("Optimal cost (Dijkstra):", optimal_cost)
    if cost == optimal_cost:
        print("Verification: A* path cost matches optimal cost.")
    else:
        print("Verification: A* path cost does NOT match optimal cost.")

if __name__ == "__main__":
    main()
