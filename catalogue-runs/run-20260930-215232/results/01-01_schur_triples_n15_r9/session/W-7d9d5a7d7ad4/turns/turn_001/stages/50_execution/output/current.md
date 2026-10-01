#!/usr/bin/env python3
import json

L = [71, 97, 54, 56, 44, 158, 45, 58, 82, 135, 113, 117, 86, 40, 12, 185, 63, 50, 111, 72, 90, 109, 61, 13, 92, 60, 91, 35, 114, 94, 105, 26, 15, 51, 102, 118, 76, 32, 108, 23, 22, 134, 83, 43, 64]
Lset = set(L)
triples = []
n = len(L)
for i in range(n):
    a = L[i]
    for j in range(i+1, n):
        b = L[j]
        c = a + b
        if c in Lset and c != a and c != b:
            triples.append((a, b, c))

num_to_triples = {x: [] for x in L}
for t in triples:
    a, b, c = t
    num_to_triples[a].append(t)
    num_to_triples[b].append(t)
    num_to_triples[c].append(t)

def search(used, solution):
    if len(used) == n:
        return solution
    candidates = [x for x in L if x not in used]
    def avail_count(x):
        return sum(1 for t in num_to_triples[x] if all(v not in used for v in t))
    candidates.sort(key=avail_count)
    v = candidates[0]
    for t in num_to_triples[v]:
        a, b, c = t
        if a in used or b in used or c in used:
            continue
        res = search(used | {a, b, c}, solution + [t])
        if res:
            return res
    return None

solution = search(set(), [])
if solution is None:
    print('WITNESS: ' + json.dumps({'found': False}))
else:
    sol_json = [[a, b, c] for a, b, c in solution]
    print('WITNESS: ' + json.dumps({'found': True, 'triples': sol_json}))

```json
{
  "files": [
    {
      "filename": "solver.py",
      "satisfies": [
        "R1",
        "R2",
        "R3",
        "R4",
        "R5",
        "R6"
      ],
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": null
      }
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": null
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": null
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": null
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": null
      }
    },
    {
      "requirement": "R5",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": null
      }
    },
    {
      "requirement": "R6",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": null
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
      "found": true,
      "triples": [
        [
          71,
          26,
          97
        ],
        [
          50,
          61,
          111
        ],
        [
          92,
          22,
          114
        ],
        [
          45,
          113,
          158
        ],
        [
          44,
          91,
          135
        ],
        [
          13,
          43,
          56
        ],
        [
          76,
          32,
          108
        ],
        [
          12,
          60,
          72
        ],
        [
          90,
          15,
          105
        ],
        [
          82,
          35,
          117
        ],
        [
          58,
          51,
          109
        ],
        [
          63,
          23,
          86
        ],
        [
          102,
          83,
          185
        ],
        [
          54,
          64,
          118
        ],
        [
          40,
          94,
          134
        ]
      ]
    },
    "provisional": false
  }
}
```
