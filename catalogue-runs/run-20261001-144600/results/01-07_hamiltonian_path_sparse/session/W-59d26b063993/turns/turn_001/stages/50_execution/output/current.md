import json

edges = [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11), (0,3), (2,7), (4,9), (6,11), (1,8)]

# Build adjacency list for the undirected graph
adj = {i: set() for i in range(12)}
for u, v in edges:
    adj[u].add(v)
    adj[v].add(u)

def backtrack(path, visited):
    """Recursively extend a partial Hamiltonian path.
    Returns a complete path (list of 12 nodes) if found, otherwise None.
    """
    if len(path) == 12:
        return path
    last = path[-1]
    for nxt in adj[last]:
        if nxt not in visited:
            visited.add(nxt)
            path.append(nxt)
            result = backtrack(path, visited)
            if result is not None:
                return result
            path.pop()
            visited.remove(nxt)
    return None

solution = None
# Try each node as a starting point
for start in range(12):
    visited = {start}
    path = [start]
    solution = backtrack(path, visited)
    if solution:
        break

if solution:
    # Verify the path really is Hamiltonian
    assert len(solution) == 12
    for i in range(11):
        assert solution[i+1] in adj[solution[i]]
    witness = {"polarity": "positive", "data": {"path": solution}}
else:
    # Should not happen for this graph, but provide a negative witness for completeness
    witness = {
        "polarity": "negative",
        "basis": "search",
        "search_exhausted": True,
        "nodes_explored": 0,
        "method": "backtracking",
        "argument": "",
        "evidence": {"path": ""},
        "provisional": False
    }
print("WITNESS: " + json.dumps(witness))

```json
{
  "files": [],
  "reconciliation": [],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "data": {
      "path": [
        0,
        1,
        8,
        9,
        10,
        11,
        6,
        5,
        4,
        3,
        2,
        7
      ]
    },
    "provisional": false
  }
}
```
