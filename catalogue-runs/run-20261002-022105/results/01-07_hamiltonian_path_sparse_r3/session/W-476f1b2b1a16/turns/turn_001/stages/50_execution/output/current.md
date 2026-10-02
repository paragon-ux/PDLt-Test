import json
from itertools import permutations

def find_hamiltonian_path():
    nodes = list(range(12))
    edges = {(0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(9,10),(10,11),(0,3),(2,7),(4,9),(6,11),(1,8)}
    # undirected edges
    adj = {i:set() for i in nodes}
    for u,v in edges:
        adj[u].add(v)
        adj[v].add(u)
    # backtracking
    visited = [False]*12
    path = []
    def backtrack(cur):
        if len(path)==12:
            return True
        for nxt in adj[cur]:
            if not visited[nxt]:
                visited[nxt]=True
                path.append(nxt)
                if backtrack(nxt):
                    return True
                path.pop()
                visited[nxt]=False
        return False
    for start in nodes:
        visited[start]=True
        path=[start]
        if backtrack(start):
            return path
        visited[start]=False
    return None

path = find_hamiltonian_path()
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
        "nodes_explored": None,
        "method": "backtracking",
        "argument": None,
        "domain": None,
        "provisional": None
    }
print("WITNESS: " + json.dumps(witness))

[host] Witness values are written into the program, not computed; unverified.

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
      ]
    },
    "provisional": true
  }
}
```
