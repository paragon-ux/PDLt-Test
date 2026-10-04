# Correct with a different interface: returns a dict, raises when there is no path.
import heapq


class NoPath(Exception):
    pass


def find_path(grid, start, goal):
    start, goal = tuple(start), tuple(goal)
    dist, prev, seen = {start: 0}, {}, set()
    pq = [(abs(start[0] - goal[0]) + abs(start[1] - goal[1]), start)]
    while pq:
        _, cur = heapq.heappop(pq)
        if cur in seen:
            continue
        seen.add(cur)
        if cur == goal:
            path = [cur]
            while path[-1] != start:
                path.append(prev[path[-1]])
            return {"path": list(reversed(path)), "cost": dist[goal]}
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            nxt = (cur[0] + dr, cur[1] + dc)
            if 0 <= nxt[0] < len(grid) and 0 <= nxt[1] < len(grid[0]) and grid[nxt[0]][nxt[1]] != -1:
                nd = dist[cur] + grid[nxt[0]][nxt[1]]
                if nd < dist.get(nxt, float("inf")):
                    dist[nxt], prev[nxt] = nd, cur
                    heapq.heappush(pq, (nd + abs(nxt[0] - goal[0]) + abs(nxt[1] - goal[1]), nxt))
    raise NoPath(f"no path from {start} to {goal}")
