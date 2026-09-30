# Hamiltonian path search for the given graph
# Nodes: 0-11
# Edges as undirected pairs
edges = [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11), (0,3), (2,7), (4,9), (6,11), (1,8)]

# Build adjacency list
adj = {i: set() for i in range(12)}
for u, v in edges:
    adj[u].add(v)
    adj[v].add(u)

solution = None

def backtrack(path, visited):
    global solution
    if solution is not None:
        return True
    if len(path) == 12:
        solution = path.copy()
        return True
    last = path[-1]
    for nxt in sorted(adj[last]):
        if nxt not in visited:
            visited.add(nxt)
            path.append(nxt)
            if backtrack(path, visited):
                return True
            path.pop()
            visited.remove(nxt)
    return False

# Try each possible start node
for start in range(12):
    if backtrack([start], {start}):
        break

if solution is not None:
    print("Hamiltonian path found:", solution)
    import json, sys
    witness = {
        "polarity": "positive",
        "evidence": {"path": "execution://witness"},
        "data": {"path": solution}
    }
    print("WITNESS: " + json.dumps(witness))
else:
    print("No Hamiltonian path exists.")
    import json, sys
    witness = {
        "polarity": "negative",
        "evidence": {"path": "execution://witness"},
        "basis": "search",
        "search_exhausted": true,
        "nodes_explored": 0,
        "method": "backtrack"
    }
    print("WITNESS: " + json.dumps(witness))

```json
{
  "files": [
    {
      "filename": "hamiltonian_path.py",
      "satisfies": [
        "R1",
        "R2",
        "R3",
        "R4",
        "R5"
      ],
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "# Hamiltonian path search for the given graph"
      }
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "edges = [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11), (0,3), (2,7), (4,9), (6,11), (1,8)]"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "def backtrack(path, visited):"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "if len(path) == 12:"
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "if nxt not in visited:"
      }
    },
    {
      "requirement": "R5",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "print(\"Hamiltonian path found:\", solution)"
      }
    }
  ],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "evidence": {
      "path": "execution://witness"
    },
    "data": {
      "path": [
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
