import heapq


def a_star(grid, start, goal):
    rows, cols = len(grid), len(grid[0])

    def h(cell):
        return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])

    g = {start: 0}
    came = {}
    heap = [(h(start), 0, start)]
    while heap:
        _, cost, cell = heapq.heappop(heap)
        if cell == goal:
            path = [cell]
            while cell in came:
                cell = came[cell]
                path.append(cell)
            return path[::-1], cost
        if cost > g[cell]:
            continue
        r, c = cell
        for nxt in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            nr, nc = nxt
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] >= 0:
                new = cost + grid[nr][nc]
                if new < g.get(nxt, float("inf")):
                    g[nxt], came[nxt] = new, cell
                    heapq.heappush(heap, (new + h(nxt), new, nxt))
    return None, float("inf")
