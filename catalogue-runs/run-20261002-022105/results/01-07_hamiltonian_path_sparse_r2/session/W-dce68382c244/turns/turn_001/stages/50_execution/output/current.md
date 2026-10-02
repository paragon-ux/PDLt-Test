import json

# Graph definition
edges = [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11),
         (0,3), (2,7), (4,9), (6,11), (1,8)]

# Build adjacency list
adj = {i: set() for i in range(12)}
for u, v in edges:
    adj[u].add(v)
    adj[v].add(u)

found_path = None
nodes_explored = 0

def backtrack(path, visited):
    global found_path, nodes_explored
    if found_path is not None:
        return True
    nodes_explored += 1
    if len(path) == 12:
        found_path = path[:]
        return True
    last = path[-1]
    for nxt in adj[last]:
        if nxt not in visited:
            visited.add(nxt)
            path.append(nxt)
            # simple pruning: if remaining unvisited nodes are disconnected from current frontier, abort
            # Here we skip sophisticated pruning for brevity
            if backtrack(path, visited):
                return True
            path.pop()
            visited.remove(nxt)
    return False

# Try each start node
for start in range(12):
    backtrack([start], {start})
    if found_path:
        break

if found_path:
    # Verify path
    assert len(found_path) == 12
    for a, b in zip(found_path, found_path[1:]):
        assert b in adj[a]
    witness = {
        "polarity": "positive",
        "data": {
            "hamiltonian_path": found_path
        }
    }
    print("WITNESS: " + json.dumps(witness))
else:
    witness = {
        "polarity": "negative",
        "basis": "search",
        "search_exhausted": True,
        "nodes_explored": nodes_explored,
        "method": "backtracking"
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
