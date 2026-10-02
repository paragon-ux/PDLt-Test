# Kahn's algorithm with cycle detection

def kahn_topological_sort(adj):
    """Return a topological ordering if the graph is a DAG.
    If a cycle exists, return a tuple (False, cycle_list) where cycle_list
    is the sequence of nodes forming a cycle.
    adj: dict mapping node -> list of successors.
    """
    # Compute indegrees
    indegree = {u: 0 for u in adj}
    for u in adj:
        for v in adj[u]:
            indegree.setdefault(v, 0)
            indegree[v] += 1
    # Initialize queue with nodes of indegree 0
    queue = [u for u, deg in indegree.items() if deg == 0]
    order = []
    while queue:
        u = queue.pop(0)
        order.append(u)
        for v in adj.get(u, []):
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    if len(order) == len(indegree):
        return (True, order)
    # Cycle detection: find a cycle using DFS
    visited = set()
    stack = []
    onstack = set()
    def dfs(u):
        visited.add(u)
        stack.append(u)
        onstack.add(u)
        for v in adj.get(u, []):
            if v not in visited:
                result = dfs(v)
                if result:
                    return result
            elif v in onstack:
                # cycle found, extract cycle
                idx = stack.index(v)
                return stack[idx:] + [v]
        stack.pop()
        onstack.remove(u)
        return None
    for node in indegree:
        if node not in visited:
            cycle = dfs(node)
            if cycle:
                return (False, cycle)
    return (False, [])

# Test cases
if __name__ == "__main__":
    # (a) DAG with 8 nodes
    dag = {
        1: [2, 3],
        2: [4],
        3: [4, 5],
        4: [6],
        5: [6],
        6: [7, 8],
        7: [],
        8: []
    }
    ok, result = kahn_topological_sort(dag)
    print("DAG result:", result)
    # Verify ordering respects edges
    def respects(order, graph):
        pos = {node: i for i, node in enumerate(order)}
        for u, outs in graph.items():
            for v in outs:
                if pos[u] > pos[v]:
                    return False
        return True
    assert ok and respects(result, dag), "DAG ordering invalid"

    # (b) Graph with a cycle
    cyclic = {
        'A': ['B'],
        'B': ['C'],
        'C': ['D'],
        'D': ['B']  # cycle B -> C -> D -> B
    }
    ok2, result2 = kahn_topological_sort(cyclic)
    print("Cyclic result:", result2)
    assert not ok2 and isinstance(result2, list) and len(result2) > 0, "Cycle not detected"
