# Correct with a different interface: returns (order, None) for a DAG and
# (None, cycle) for a cyclic graph instead of raising.
def kahn(adjacency):
    from collections import deque

    nodes = list(dict.fromkeys(list(adjacency) + [v for vs in adjacency.values() for v in vs]))
    indeg = {n: 0 for n in nodes}
    for vs in adjacency.values():
        for v in vs:
            indeg[v] += 1
    q = deque(n for n in nodes if indeg[n] == 0)
    order = []
    while q:
        n = q.popleft()
        order.append(n)
        for v in adjacency.get(n, []):
            indeg[v] -= 1
            if not indeg[v]:
                q.append(v)
    if len(order) == len(nodes):
        return order, None
    color, stack = {}, []

    def dfs(n):
        color[n] = 1
        stack.append(n)
        for v in adjacency.get(n, []):
            if indeg.get(v, 0) <= 0:
                continue
            if color.get(v) == 1:
                return stack[stack.index(v):]
            if v not in color:
                found = dfs(v)
                if found:
                    return found
        stack.pop()
        color[n] = 2
        return None

    for n in nodes:
        if indeg[n] > 0 and n not in color:
            cycle = dfs(n)
            if cycle:
                return None, cycle
    return None, []
