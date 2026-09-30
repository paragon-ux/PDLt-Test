# kahn_topo.py
"""Implementation of Kahn's algorithm for topological sorting with cycle detection.
Provides two test cases as required by the confirmed prompt.
"""
from collections import deque
from typing import Dict, List, Tuple, Union

def kahn_topological_sort(adj: Dict[int, List[int]]) -> Union[List[int], Tuple[str, List[int]]]:
    """Return a topological ordering of the directed graph given as an adjacency list.
    If a cycle exists, return a tuple ("cycle", cycle_nodes) where cycle_nodes is a list
    of node identifiers forming one detected cycle.
    """
    # Compute in-degree of each node
    indegree = {u: 0 for u in adj}
    for u, neighbors in adj.items():
        for v in neighbors:
            indegree.setdefault(v, 0)
            indegree[v] += 1
    # Queue of nodes with zero indegree
    queue = deque([u for u, deg in indegree.items() if deg == 0])
    order: List[int] = []
    # Track processed edges to later detect cycle nodes
    processed_edges = set()
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in adj.get(u, []):
            processed_edges.add((u, v))
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    # If all edges processed, graph is acyclic
    if len(processed_edges) == sum(len(v) for v in adj.values()):
        return order
    # Cycle detection: find a node that still has indegree > 0 and follow back edges
    # Simple DFS to extract one cycle
    visited = set()
    stack = []
    on_stack = set()
    cycle: List[int] = []
    def dfs(u: int) -> bool:
        visited.add(u)
        stack.append(u)
        on_stack.add(u)
        for v in adj.get(u, []):
            if (u, v) in processed_edges:
                continue  # skip processed (acyclic) edges
            if v not in visited:
                if dfs(v):
                    return True
            elif v in on_stack:
                # Found a cycle; extract it
                idx = stack.index(v)
                cycle.extend(stack[idx:])
                return True
        stack.pop()
        on_stack.remove(u)
        return False
    for node in indegree:
        if indegree[node] > 0 and node not in visited:
            if dfs(node):
                break
    return ("cycle", cycle)

# ==== Test cases ====

def test_valid_dag():
    # Eight-node DAG
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
    result = kahn_topological_sort(graph)
    assert isinstance(result, list), "Expected a list for DAG"
    # Verify ordering respects edges
    position = {node: idx for idx, node in enumerate(result)}
    for u, deps in graph.items():
        for v in deps:
            assert position[u] < position[v], f"Edge {u}->{v} violated in ordering"
    print("Valid DAG test passed. Ordering:", result)

def test_cycle_graph():
    # Graph with a cycle: 1 -> 2 -> 3 -> 1
    graph = {
        1: [2],
        2: [3],
        3: [1, 4],
        4: []
    }
    result = kahn_topological_sort(graph)
    assert isinstance(result, tuple) and result[0] == "cycle", "Expected a cycle report"
    cycle_nodes = result[1]
    # Verify that reported nodes indeed form a cycle
    assert len(cycle_nodes) >= 2, "Cycle must contain at least two nodes"
    # Check closure of cycle
    for i in range(len(cycle_nodes)):
        u = cycle_nodes[i]
        v = cycle_nodes[(i + 1) % len(cycle_nodes)]
        assert v in graph.get(u, []), f"Reported nodes {u}->{v} not an edge in graph"
    print("Cycle detection test passed. Cycle:", cycle_nodes)

if __name__ == "__main__":
    test_valid_dag()
    test_cycle_graph()
