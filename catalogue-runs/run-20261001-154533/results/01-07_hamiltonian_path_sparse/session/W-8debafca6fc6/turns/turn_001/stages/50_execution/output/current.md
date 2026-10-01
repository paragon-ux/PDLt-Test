import json
from collections import defaultdict

def find_hamiltonian_path(edges, n):
    adj = defaultdict(set)
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    path = []
    visited = [False]*n
    nodes_explored = 0
    def backtrack(u, depth):
        nonlocal nodes_explored
        nodes_explored += 1
        path.append(u)
        visited[u] = True
        if depth == n:
            return True
        for v in sorted(adj[u]):
            if not visited[v]:
                if backtrack(v, depth+1):
                    return True
        visited[u] = False
        path.pop()
        return False
    for start in range(n):
        # reset for each start
        path.clear()
        visited = [False]*n
        if backtrack(start, 1):
            return path, nodes_explored
    return None, nodes_explored

edges = [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11), (0,3), (2,7), (4,9), (6,11), (1,8)]
N = 12
path, explored = find_hamiltonian_path(edges, N)
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
