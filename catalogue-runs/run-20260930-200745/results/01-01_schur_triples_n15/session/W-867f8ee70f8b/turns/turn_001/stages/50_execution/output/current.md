import sys, json
L = [71, 97, 54, 56, 44, 158, 45, 58, 82, 135, 113, 117, 86, 40, 12, 185, 63, 50, 111, 72, 90, 109, 61, 13, 92, 60, 91, 35, 114, 94, 105, 26, 15, 51, 102, 118, 76, 32, 108, 23, 22, 134, 83, 43, 64]
Lset = set(L)
# generate all valid triples (a,b,c) with a+b=c and distinct elements
triples = []
for c in L:
    for a in L:
        if a >= c:
            continue
        b = c - a
        if b in Lset and b != a and b != c:
            # enforce ordering to avoid duplicate permutations
            if a < b:
                triples.append((a, b, c))
# map element -> list of triples indices covering it
elem_to_triples = {x: [] for x in L}
for idx, (a, b, c) in enumerate(triples):
    for x in (a, b, c):
        elem_to_triples[x].append(idx)
solution = []
used = set()

sys.setrecursionlimit(10000)

def backtrack():
    if len(used) == len(L):
        return True
    # choose uncovered element with fewest candidate triples
    uncovered = [x for x in L if x not in used]
    elem = min(uncovered, key=lambda e: len([t for t in elem_to_triples[e] if not any(v in used for v in triples[t])]))
    for t_idx in elem_to_triples[elem]:
        a, b, c = triples[t_idx]
        if a in used or b in used or c in used:
            continue
        # select
        used.update([a, b, c])
        solution.append((a, b, c))
        if backtrack():
            return True
        # backtrack
        used.difference_update([a, b, c])
        solution.pop()
    return False

found = backtrack()
if found:
    witness = {"polarity": "positive", "evidence": {"path": "execution://witness"}, "data": {"triples": solution}}
else:
    witness = {"polarity": "negative", "evidence": {"path": "execution://witness"}, "basis": "search", "search_exhausted": true, "nodes_explored": null, "method": "backtrack"}
print("WITNESS: " + json.dumps(witness))

```json
{
  "files": [
    {
      "filename": "triple_solution.py",
      "satisfies": [
        "R1"
      ],
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "import sys, json"
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
        "observed": "WITNESS: "
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
      "triples": [
        [
          26,
          71,
          97
        ],
        [
          50,
          61,
          111
        ],
        [
          43,
          92,
          135
        ],
        [
          12,
          44,
          56
        ],
        [
          32,
          58,
          90
        ],
        [
          15,
          102,
          117
        ],
        [
          45,
          63,
          108
        ],
        [
          22,
          91,
          113
        ],
        [
          72,
          86,
          158
        ],
        [
          23,
          82,
          105
        ],
        [
          76,
          109,
          185
        ],
        [
          13,
          51,
          64
        ],
        [
          54,
          60,
          114
        ],
        [
          40,
          94,
          134
        ],
        [
          35,
          83,
          118
        ]
      ]
    },
    "provisional": false
  }
}
```
