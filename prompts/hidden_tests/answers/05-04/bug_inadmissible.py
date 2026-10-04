# Wrong: a greedy best-first search (heuristic only, ignoring cost so far) that
# stops at the first time it reaches the goal, so paths are not cost-optimal.
import heapq


def a_star(grid, start, goal):
    def h(c):
        return abs(c[0] - goal[0]) + abs(c[1] - goal[1])

    came, seen = {}, {start}
    heap = [(h(start), start)]
    while heap:
        _, cell = heapq.heappop(heap)
        if cell == goal:
            path = [cell]
            while cell in came:
                cell = came[cell]
                path.append(cell)
            path.reverse()
            return path, sum(grid[r][c] for r, c in path[1:])
        r, c = cell
        for nxt in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nxt[0] < len(grid) and 0 <= nxt[1] < len(grid[0]) and grid[nxt[0]][nxt[1]] >= 0 \
                    and nxt not in seen:
                seen.add(nxt)
                came[nxt] = cell
                heapq.heappush(heap, (h(nxt), nxt))
    return None, float("inf")
