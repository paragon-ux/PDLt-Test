import json
from collections import defaultdict

# Graph definition
edges = [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11), (0,3), (2,7), (4,9), (6,11), (1,8)]

adj = defaultdict(set)
for u,v in edges:
    adj[u].add(v)
    adj[v].add(u)

N = 12

found_path = None
states_explored = 0

def backtrack(path, visited):
    global found_path, states_explored
    states_explored += 1
    if found_path is not None:
        return True
    if len(path) == N:
        found_path = path.copy()
        return True
    last = path[-1]
    for nxt in adj[last]:
        if nxt not in visited:
            visited.add(nxt)
            path.append(nxt)
            if backtrack(path, visited):
                return True
            path.pop()
            visited.remove(nxt)
    return False

# Try starting from each node
for start in range(N):
    if found_path:
        break
    backtrack([start], {start})

if found_path:
    # Verify
    assert len(found_path) == N
    for i in range(N-1):
        assert found_path[i+1] in adj[found_path[i]]
    witness = {
        "polarity": "positive",
        "data": {"hamiltonian_path": found_path}
    }
else:
    witness = {
        "polarity": "negative",
        "basis": "search",
        "search_exhausted": True,
        "nodes_explored": states_explored,
        "method": "backtracking",
        "argument": None,
        "domain": None,
        "provisional": False
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
