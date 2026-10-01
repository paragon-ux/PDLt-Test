import sys
from collections import deque

def kahn_topological_sort(adj_list):
    """Return a topological order of the directed graph represented by adj_list.
    If a cycle exists, raise a ValueError with the cycle nodes listed.

    Parameters
    ----------
    adj_list : dict
        Mapping from node to iterable of successor nodes.
    """
    # Build indegree map
    indegree = {node: 0 for node in adj_list}
    for u, neighbors in adj_list.items():
        for v in neighbors:
            indegree.setdefault(v, 0)
            indegree[v] += 1
    # Queue of nodes with indegree 0
    zero_queue = deque([n for n, d in indegree.items() if d == 0])
    topo_order = []
    while zero_queue:
        u = zero_queue.popleft()
        topo_order.append(u)
        for v in adj_list.get(u, []):
            indegree[v] -= 1
            if indegree[v] == 0:
                zero_queue.append(v)
    if len(topo_order) != len(indegree):
        # Cycle detection: find one cycle using DFS
        def find_cycle():
            visited = set()
            stack = []
            on_stack = set()
            def dfs(node):
                visited.add(node)
                stack.append(node)
                on_stack.add(node)
                for neigh in adj_list.get(node, []):
                    if neigh not in visited:
                        result = dfs(neigh)
                        if result:
                            return result
                    elif neigh in on_stack:
                        # Cycle found, extract cycle sequence
                        idx = stack.index(neigh)
                        return stack[idx:] + [neigh]
                stack.pop()
                on_stack.remove(node)
                return None
            for n in indegree:
                if n not in visited:
                    cyc = dfs(n)
                    if cyc:
                        return cyc
            return []
        cycle = find_cycle()
        raise ValueError(f"Cycle detected: {' -> '.join(map(str, cycle))}")
    return topo_order

def _test():
    # Test 1: valid DAG with 8 nodes
    dag = {
        1: [2, 3],
        2: [4],
        3: [4, 5],
        4: [6],
        5: [6, 7],
        6: [8],
        7: [8],
        8: []
    }
    order = kahn_topological_sort(dag)
    # Verify ordering respects edges
    position = {node: i for i, node in enumerate(order)}
    for u, vs in dag.items():
        for v in vs:
            assert position[u] < position[v], f"Edge {u}->{v} violated"
    print("DAG test passed. Order:", order)

    # Test 2: graph with a cycle
    cyclic = {
        'A': ['B'],
        'B': ['C'],
        'C': ['D'],
        'D': ['B']  # cycle B->C->D->B
    }
    try:
        kahn_topological_sort(cyclic)
    except ValueError as e:
        print("Cycle test passed. Detected:", e)
    else:
        assert False, "Cycle not detected"

if __name__ == "__main__":
    _test()
