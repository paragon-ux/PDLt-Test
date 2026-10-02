#!/usr/bin/env python3
import json, itertools, sys

L = {71, 97, 54, 56, 44, 158, 45, 58, 82, 135, 113, 117, 86, 40, 12, 185, 63, 50, 111, 72, 90, 109, 61, 13, 92, 60, 91, 35, 114, 94, 105, 26, 15, 51, 102, 118, 76, 32, 108, 23, 22, 134, 83, 43, 64}

# Precompute all valid triples (a,b,c) with a+b=c
triples = []
for a, b in itertools.combinations(L, 2):
    c = a + b
    if c in L and c != a and c != b:
        triples.append((a, b, c))

# Build a mapping from element to triples containing it for quick lookup
from collections import defaultdict
elem_to_triples = defaultdict(list)
for t in triples:
    for x in t:
        elem_to_triples[x].append(t)

# Backtracking search for exact cover of 15 triples
solution = []
used = set()
nodes_explored = 0

def backtrack():
    global nodes_explored
    if len(solution) == 15:
        return True
    # choose an unused element with fewest candidate triples to branch
    candidates = [e for e in L if e not in used]
    if not candidates:
        return False
    e = min(candidates, key=lambda x: len([t for t in elem_to_triples[x] if all(y not in used for y in t)]))
    possible = [t for t in elem_to_triples[e] if all(y not in used for y in t)]
    for t in possible:
        nodes_explored += 1
        solution.append(t)
        used.update(t)
        if backtrack():
            return True
        # backtrack
        solution.pop()
        used.difference_update(t)
    return False

found = backtrack()

if found:
    witness = {
        "polarity": "positive",
        "data": {"triples": solution}
    }
else:
    witness = {
        "polarity": "negative",
        "basis": "search",
        "search_exhausted": True,
        "nodes_explored": nodes_explored,
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
      "triples": [
        [
          13,
          92,
          105
        ],
        [
          12,
          97,
          109
        ],
        [
          15,
          43,
          58
        ],
        [
          56,
          102,
          158
        ],
        [
          22,
          61,
          83
        ],
        [
          32,
          86,
          118
        ],
        [
          35,
          82,
          117
        ],
        [
          26,
          50,
          76
        ],
        [
          45,
          63,
          108
        ],
        [
          64,
          71,
          135
        ],
        [
          44,
          90,
          134
        ],
        [
          23,
          91,
          114
        ],
        [
          40,
          54,
          94
        ],
        [
          51,
          60,
          111
        ],
        [
          72,
          113,
          185
        ]
      ]
    },
    "provisional": false
  }
}
```
