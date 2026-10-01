# Python script to find a 4-coloring of the wheel graph W_11 and emit a witness
import json

# Define the wheel graph W_11
nodes = list(range(12))  # 0 is hub, 1-11 are outer cycle
edges = []
# Hub edges
for i in range(1, 12):
    edges.append((0, i))
# Outer cycle edges
for i in range(1, 12):
    edges.append((i, i % 11 + 1))

# Colors available
colors = [1, 2, 3, 4]

# Adjacency dictionary
adj = {n: set() for n in nodes}
for u, v in edges:
    adj[u].add(v)
    adj[v].add(u)

# Backtracking search for a valid 4-coloring
solution = {}

def backtrack(node_index):
    if node_index == len(nodes):
        return True
    node = nodes[node_index]
    for c in colors:
        if all(solution.get(nb) != c for nb in adj[node]):
            solution[node] = c
            if backtrack(node_index + 1):
                return True
            del solution[node]
    return False

found = backtrack(0)

# Prepare witness data
if found:
    witness = {
        "polarity": "positive",
        "data": {
            "description": "A valid 4-coloring for W_11",
            "coloring": solution,
            "proof_3_insufficient": "Wheel graph W_n is 4‑chromatic when n is odd. The outer cycle of length 11 is odd, so any proper coloring of the outer cycle needs at least 3 colors, and the hub adjacent to all outer vertices forces a fourth distinct color. Hence 3 colors are insufficient."
        }
    }
else:
    # This branch should never happen for 4 colors
    witness = {
        "polarity": "negative",
        "basis": "search",
        "search_exhausted": True,
        "nodes_explored": 0,
        "method": "backtrack",
        "argument": None,
        "domain": None,
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
      "description": "A valid 4-coloring for W_11",
      "coloring": {
        "0": 1,
        "1": 2,
        "2": 3,
        "3": 2,
        "4": 3,
        "5": 2,
        "6": 3,
        "7": 2,
        "8": 3,
        "9": 2,
        "10": 3,
        "11": 4
      },
      "proof_3_insufficient": "Wheel graph W_n is 4‑chromatic when n is odd. The outer cycle of length 11 is odd, so any proper coloring of the outer cycle needs at least 3 colors, and the hub adjacent to all outer vertices forces a fourth distinct color. Hence 3 colors are insufficient."
    },
    "provisional": false
  }
}
```
