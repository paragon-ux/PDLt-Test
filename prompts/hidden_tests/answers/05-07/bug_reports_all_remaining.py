# Wrong: on a cycle it reports every node left with in-degree > 0, which includes
# nodes downstream of the cycle, not the cycle itself.
def topological_sort(graph):
    nodes = set(graph) | {v for vs in graph.values() for v in vs}
    indeg = {n: 0 for n in nodes}
    for vs in graph.values():
        for v in vs:
            indeg[v] += 1
    ready = sorted(n for n in nodes if indeg[n] == 0)
    order = []
    while ready:
        n = ready.pop(0)
        order.append(n)
        for v in graph.get(n, ()):
            indeg[v] -= 1
            if indeg[v] == 0:
                ready.append(v)
    if len(order) < len(nodes):
        raise ValueError(f"cycle among: {sorted(n for n in nodes if indeg[n] > 0)}")
    return order
