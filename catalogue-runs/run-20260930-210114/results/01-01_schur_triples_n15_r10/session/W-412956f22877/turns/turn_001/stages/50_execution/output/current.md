# Python script to find a partition of the given list into triples (a,b,c) with a+b=c
L = {71, 97, 54, 56, 44, 158, 45, 58, 82, 135, 113, 117, 86, 40, 12, 185, 63, 50, 111, 72, 90, 109, 61, 13, 92, 60, 91, 35, 114, 94, 105, 26, 15, 51, 102, 118, 76, 32, 108, 23, 22, 134, 83, 43, 64}

# Pre‑compute all valid triples (a,b,c) with a<b and a+b=c
triples = []
for a in L:
    for b in L:
        if a < b:
            c = a + b
            if c in L and c != a and c != b:
                triples.append((a, b, c))

# Build adjacency: for each number, which triples contain it
from collections import defaultdict
num_to_triples = defaultdict(list)
for idx, t in enumerate(triples):
    for n in t:
        num_to_triples[n].append(idx)

# Recursive exact‑cover search (depth‑first, choose the number with fewest candidate triples)
used = set()
solution = []

def search():
    if len(used) == len(L):
        return True
    # pick an uncovered number with fewest options
    uncovered = [n for n in L if n not in used]
    n = min(uncovered, key=lambda x: len([ti for ti in num_to_triples[x] if not any(v in used for v in triples[ti])]))
    for ti in num_to_triples[n]:
        a,b,c = triples[ti]
        if a in used or b in used or c in used:
            continue
        used.update([a,b,c])
        solution.append((a,b,c))
        if search():
            return True
        solution.pop()
        used.difference_update([a,b,c])
    return False

found = search()
if found:
    print("Partition found:")
    for triple in solution:
        print(triple)
    import json, sys
    witness = {"polarity":"positive","evidence":{"path":"execution://witness"},"data":{"partition":solution}}
    print("WITNESS: "+json.dumps(witness))
else:
    print("No partition exists.")
    import json, sys
    witness = {"polarity":"negative","evidence":{"path":"execution://witness"},"basis":"proof","argument":"Exhaustive search found no exact‑cover; therefore no partition exists for the given set."}
    print("WITNESS: "+json.dumps(witness))

```json
{
  "files": [
    {
      "filename": "partition_finder.py",
      "satisfies": [
        "R1"
      ],
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": ""
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
        "observed": "The script computes all valid triples, performs a depth‑first exact‑cover search, and either prints a partition or a proof of impossibility."
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
      "partition": [
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
