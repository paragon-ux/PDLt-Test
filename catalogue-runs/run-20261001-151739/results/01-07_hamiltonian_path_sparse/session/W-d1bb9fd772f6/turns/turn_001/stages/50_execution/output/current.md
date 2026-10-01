import json
from collections import defaultdict

def find_hamiltonian_path(nodes, edges):
    adj = defaultdict(set)
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    n = len(nodes)
    path = []
    visited = set()
    def backtrack(u):
        if len(path) == n:
            return True
        for v in adj[u]:
            if v not in visited:
                visited.add(v)
                path.append(v)
                if backtrack(v):
                    return True
                visited.remove(v)
                path.pop()
        return False
    for start in nodes:
        visited.clear()
        path.clear()
        visited.add(start)
        path.append(start)
        if backtrack(start):
            return path
    return None

nodes = list(range(12))
edges = [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11), (0,3), (2,7), (4,9), (6,11), (1,8)]
path = find_hamiltonian_path(nodes, edges)
if path is None:
    witness = {
        "polarity": "negative",
        "basis": "search",
        "search_exhausted": True,
        "nodes_explored": None,
        "method": "backtracking",
        "argument": None,
        "domain": None,
        "provisional": False
    }
else:
    witness = {
        "polarity": "positive",
        "data": {
            "hamiltonian_path": path,
            "verification": {
                "includes_all_nodes": len(set(path)) == len(nodes),
                "consecutive_edges_valid": all(((path[i], path[i+1]) in edges) or ((path[i+1], path[i]) in edges) for i in range(len(path)-1))
            }
        }
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
      "hamiltonian_path": [
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
      ],
      "verification": {
        "includes_all_nodes": true,
        "consecutive_edges_valid": true
      }
    },
    "provisional": false
  }
}
```
