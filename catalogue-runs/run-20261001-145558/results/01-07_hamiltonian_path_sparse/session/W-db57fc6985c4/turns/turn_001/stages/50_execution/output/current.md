import json

graph_edges = {(0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(9,10),(10,11),
               (0,3),(2,7),(4,9),(6,11),(1,8)}
# make undirected
edges = set()
for u,v in graph_edges:
    edges.add((u,v))
    edges.add((v,u))

path = [0,1,2,3,4,5,6,7,8,9,10,11]
# verification
assert len(path) == 12, "Path does not include all nodes"
assert len(set(path)) == 12, "Path contains duplicate nodes"
for a,b in zip(path, path[1:]):
    assert (a,b) in edges, f"Edge ({a},{b}) not in graph"

witness = {
    "polarity": "positive",
    "data": {
        "hamiltonian_path": path
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
