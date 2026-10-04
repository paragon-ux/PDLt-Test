from collections import deque


class CycleError(Exception):
    def __init__(self, cycle):
        super().__init__(f"cycle detected: {' -> '.join(map(str, cycle + cycle[:1]))}")
        self.cycle = cycle


def topological_sort(graph):
    nodes = set(graph) | {v for vs in graph.values() for v in vs}
    indegree = {n: 0 for n in nodes}
    for vs in graph.values():
        for v in vs:
            indegree[v] += 1
    queue = deque(sorted(n for n in nodes if indegree[n] == 0))
    order = []
    while queue:
        n = queue.popleft()
        order.append(n)
        for v in graph.get(n, ()):
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    if len(order) == len(nodes):
        return order
    # Every node left has a predecessor that is also left, so walking predecessors
    # never dead-ends and must repeat a node: the loop it closes is a cycle.
    remaining = {n for n in nodes if indegree[n] > 0}
    preds = {n: [u for u, vs in graph.items() if n in vs and u in remaining] for n in remaining}
    seen, path, node = {}, [], min(remaining)
    while node not in seen:
        seen[node] = len(path)
        path.append(node)
        node = preds[node][0]
    raise CycleError(list(reversed(path[seen[node]:])))
