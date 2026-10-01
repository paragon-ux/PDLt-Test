import collections
from typing import Dict, List, Tuple, Set

class CycleError(Exception):
    """Exception raised when a cycle is detected in the graph.

    Attributes
    ----------
    cycle: List
        The sequence of nodes that form the cycle.
    """
    def __init__(self, cycle: List):
        self.cycle = cycle
        super().__init__(f"Cycle detected: {' -> '.join(map(str, cycle))}")

def kahn_topological_sort(adj: Dict) -> List:
    """Return a topological ordering of the directed graph ``adj``.

    Parameters
    ----------
    adj: dict
        Adjacency list representation where keys are node identifiers and
        values are iterables of successor nodes.

    Returns
    -------
    list
        A topological ordering of all nodes.

    Raises
    ------
    CycleError
        If the graph contains a cycle. ``CycleError.cycle`` holds the nodes of
        one detected cycle in order.
    """
    # Compute indegree of each node
    indegree: Dict = collections.defaultdict(int)
    for u in adj:
        indegree.setdefault(u, 0)
        for v in adj[u]:
            indegree[v] += 1
            indegree.setdefault(v, 0)

    # Queue of nodes with indegree 0
    queue = collections.deque([node for node, deg in indegree.items() if deg == 0])
    topo: List = []
    while queue:
        node = queue.popleft()
        topo.append(node)
        for neighbor in adj.get(node, []):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    if len(topo) == len(indegree):
        return topo
    # Cycle detection: remaining nodes have indegree > 0
    remaining: Set = {n for n in indegree if indegree[n] > 0}
    # Simple DFS to extract a cycle
    visited: Set = set()
    stack: List = []
    onstack: Set = set()
    def dfs(u):
        visited.add(u)
        stack.append(u)
        onstack.add(u)
        for v in adj.get(u, []):
            if v not in remaining:
                continue
            if v not in visited:
                result = dfs(v)
                if result:
                    return result
            elif v in onstack:
                # cycle found, extract from stack
                idx = stack.index(v)
                return stack[idx:] + [v]
        stack.pop()
        onstack.remove(u)
        return None
    for start in list(remaining):
        if start not in visited:
            cycle = dfs(start)
            if cycle:
                raise CycleError(cycle)
    # Fallback (should not happen)
    raise CycleError(list(remaining))

# ---- Tests ----
def _test_valid_dag():
    # DAG with 8 nodes
    graph = {
        1: [2, 3],
        2: [4],
        3: [4, 5],
        4: [6],
        5: [6, 7],
        6: [8],
        7: [8],
        8: []
    }
    order = kahn_topological_sort(graph)
    # Verify ordering respects edges
    position = {node: i for i, node in enumerate(order)}
    for u, neighbors in graph.items():
        for v in neighbors:
            assert position[u] < position[v], f"Edge {u}->{v} violated"
    print("Valid DAG test passed. Order:", order)

def _test_cycle():
    graph = {
        'A': ['B'],
        'B': ['C'],
        'C': ['D'],
        'D': ['B'],  # cycle B->C->D->B
        'E': []
    }
    try:
        kahn_topological_sort(graph)
    except CycleError as e:
        cycle = e.cycle
        # Verify that each consecutive pair is an edge in the graph
        for i in range(len(cycle) - 1):
            u, v = cycle[i], cycle[i + 1]
            assert v in graph.get(u, []), f"Cycle edge {u}->{v} not in graph"
        print("Cycle detection test passed. Cycle:", cycle)
    else:
        assert False, "Cycle not detected"

if __name__ == "__main__":
    _test_valid_dag()
    _test_cycle()
