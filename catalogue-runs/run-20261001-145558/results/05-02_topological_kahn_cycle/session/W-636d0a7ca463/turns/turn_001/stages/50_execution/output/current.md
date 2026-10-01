import collections

def kahn_topological_sort(adj):
    """Return a topological order of the directed graph ``adj``.
    If a cycle exists, raise ``ValueError`` with the list of nodes forming a cycle.
    ``adj`` is a dict mapping each node to an iterable of its successors.
    """
    # Compute in-degree of each node
    indegree = collections.defaultdict(int)
    for u in adj:
        indegree.setdefault(u, 0)
        for v in adj[u]:
            indegree[v] += 1
            indegree.setdefault(v, 0)
    # Queue of nodes with zero indegree
    zero = collections.deque([n for n, d in indegree.items() if d == 0])
    order = []
    while zero:
        u = zero.popleft()
        order.append(u)
        for v in adj.get(u, []):
            indegree[v] -= 1
            if indegree[v] == 0:
                zero.append(v)
    if len(order) != len(indegree):
        # Cycle detection: find one cycle using DFS on remaining nodes
        remaining = set(indegree) - set(order)
        stack = []
        visited = set()
        onstack = set()
        def dfs(node):
            visited.add(node)
            onstack.add(node)
            stack.append(node)
            for nxt in adj.get(node, []):
                if nxt not in visited:
                    if dfs(nxt):
                        return True
                elif nxt in onstack:
                    # cycle found, extract it
                    idx = stack.index(nxt)
                    cycle = stack[idx:] + [nxt]
                    raise ValueError(cycle)
            stack.pop()
            onstack.remove(node)
            return False
        for n in remaining:
            if n not in visited:
                try:
                    dfs(n)
                except ValueError as e:
                    raise ValueError(e.args[0])
        # Should not reach here
        raise ValueError(list(remaining))
    return order

# Tests
if __name__ == "__main__":
    # Test 1: valid DAG with 8 nodes
    dag = {
        'A': ['C', 'D'],
        'B': ['D', 'E'],
        'C': ['F'],
        'D': ['F', 'G'],
        'E': ['G'],
        'F': ['H'],
        'G': ['H'],
        'H': []
    }
    order = kahn_topological_sort(dag)
    print("Topological order for DAG:", order)
    # Verify order respects edges
    pos = {node: i for i, node in enumerate(order)}
    for u, outs in dag.items():
        for v in outs:
            assert pos[u] < pos[v], f"Edge {u}->{v} violated"
    print("DAG test passed.")

    # Test 2: graph with a cycle
    cyclic = {
        1: [2],
        2: [3],
        3: [4],
        4: [2]  # cycle 2->3->4->2
    }
    try:
        kahn_topological_sort(cyclic)
    except ValueError as e:
        cycle = e.args[0]
        print("Detected cycle:", cycle)
        # Verify that each consecutive pair is an edge
        for a, b in zip(cycle, cycle[1:]):
            assert b in cyclic[a], f"Missing edge {a}->{b} in reported cycle"
        print("Cycle test passed.")
    else:
        raise AssertionError("Cycle not detected")
