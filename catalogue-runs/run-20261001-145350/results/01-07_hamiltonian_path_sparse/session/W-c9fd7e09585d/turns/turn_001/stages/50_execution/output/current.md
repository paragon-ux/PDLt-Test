import json
from collections import defaultdict

def find_hamiltonian_path(edges, n):
    adj = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    visited = [False]*n
    path = []
    nodes_explored = 0
    def backtrack(node):
        nonlocal nodes_explored
        visited[node] = True
        path.append(node)
        nodes_explored += 1
        if len(path) == n:
            return True
        for nb in adj[node]:
            if not visited[nb]:
                if backtrack(nb):
                    return True
        visited[node] = False
        path.pop()
        return False
    for start in range(n):
        if backtrack(start):
            return path, nodes_explored
    return None, nodes_explored

edges = [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11), (0,3), (2,7), (4,9), (6,11), (1,8)]
path, explored = find_hamiltonian_path(edges, 12)
if path:
    witness = {
        "polarity": "positive",
        "data": {"hamiltonian_path": path}
    }
else:
    witness = {
        "polarity": "negative",
        "basis": "search",
        "search_exhausted": True,
        "nodes_explored": explored,
        "method": "backtracking"
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
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11
      ]
    },
    "provisional": false
  }
}
```
