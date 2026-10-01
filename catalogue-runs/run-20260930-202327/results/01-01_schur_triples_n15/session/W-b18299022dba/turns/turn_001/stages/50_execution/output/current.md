import itertools, json, sys

L = {71, 97, 54, 56, 44, 158, 45, 58, 82, 135, 113, 117, 86, 40, 12, 185, 63, 50, 111, 72, 90, 109, 61, 13, 92, 60, 91, 35, 114, 94, 105, 26, 15, 51, 102, 118, 76, 32, 108, 23, 22, 134, 83, 43, 64}

# Precompute all valid triples (a,b,c) with a<b and a+b=c
triples = []
for a, b in itertools.combinations(L, 2):
    c = a + b
    if c in L and c != a and c != b:
        triples.append((a, b, c))

# Build adjacency: for each element, which triples contain it
elem_to_triples = {x: [] for x in L}
for idx, t in enumerate(triples):
    for x in t:
        elem_to_triples[x].append(idx)

solution = []
used = set()

sys.setrecursionlimit(10000)

def backtrack():
    if len(used) == len(L):
        return True
    # choose unused element with fewest candidate triples (heuristic)
    remaining = [x for x in L if x not in used]
    x = min(remaining, key=lambda v: len([ti for ti in elem_to_triples[v] if all(y not in used for y in triples[ti])]))
    for ti in elem_to_triples[x]:
        a,b,c = triples[ti]
        if a in used or b in used or c in used:
            continue
        # take this triple
        solution.append((a,b,c))
        used.update([a,b,c])
        if backtrack():
            return True
        # backtrack
        solution.pop()
        used.difference_update([a,b,c])
    return False

found = backtrack()
if found:
    print("Partition found:")
    for tri in solution:
        print(tri)
    witness = {"polarity": "positive", "evidence": {"path": "execution://witness"}, "data": {"triples": solution}}
    print("WITNESS:", json.dumps(witness))
else:
    print("No partition exists.")
    witness = {"polarity": "negative", "evidence": {"path": "execution://witness"}, "basis": "search", "search_exhausted": true, "nodes_explored": null, "method": "backtrack"}
    print("WITNESS:", json.dumps(witness))

```json
{
  "files": [
    {
      "filename": "partition_search.py",
      "satisfies": [
        "R1"
      ],
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "import itertools, json, sys"
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
        "observed": "Partition found"
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
