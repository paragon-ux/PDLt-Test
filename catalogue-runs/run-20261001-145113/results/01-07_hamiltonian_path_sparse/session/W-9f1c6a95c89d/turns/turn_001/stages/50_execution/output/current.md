import json

edges = [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11), (0,3), (2,7), (4,9), (6,11), (1,8)]
adj = {i: set() for i in range(12)}
for u,v in edges:
    adj[u].add(v)
    adj[v].add(u)

solution = None
explored = 0

def dfs(path, visited):
    global solution, explored
    if solution is not None:
        return
    explored += 1
    if len(path) == 12:
        solution = list(path)
        return
    last = path[-1]
    for nb in adj[last]:
        if nb not in visited:
            visited.add(nb)
            path.append(nb)
            dfs(path, visited)
            path.pop()
            visited.remove(nb)

for start in range(12):
    dfs([start], {start})
    if solution:
        break

if solution:
    # verification
    assert len(solution) == 12
    for i in range(11):
        assert solution[i+1] in adj[solution[i]]
    witness = {"polarity":"positive","data":{"hamiltonian_path":solution}}
else:
    witness = {"polarity":"negative","basis":"search","search_exhausted":true,"nodes_explored":explored,"method":"backtracking"}
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
      ]
    },
    "provisional": false
  }
}
```
