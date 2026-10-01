import itertools, sys, json

L = {71, 97, 54, 56, 44, 158, 45, 58, 82, 135, 113, 117, 86, 40, 12, 185, 63, 50, 111, 72, 90, 109, 61, 13, 92, 60, 91, 35, 114, 94, 105, 26, 15, 51, 102, 118, 76, 32, 108, 23, 22, 134, 83, 43, 64}

# Precompute all valid triples (a,b,c) with a<b and a+b=c
triples = []
for a, b in itertools.combinations(L, 2):
    s = a + b
    if s in L:
        triples.append((a, b, s))

# Build adjacency: for each number, which triples contain it
from collections import defaultdict
num_to_triples = defaultdict(list)
for idx, t in enumerate(triples):
    for n in t:
        num_to_triples[n].append(idx)

solution = []
used = set()

sys.setrecursionlimit(10000)

def backtrack():
    if len(used) == len(L):
        return True
    # choose the unused number with fewest candidate triples (heuristic)
    candidates = [(n, len([i for i in num_to_triples[n] if all(x not in used for x in triples[i])])) for n in L if n not in used]
    n, _ = min(candidates, key=lambda x: x[1])
    for ti in num_to_triples[n]:
        a, b, c = triples[ti]
        if a in used or b in used or c in used:
            continue
        # select this triple
        solution.append((a, b, c))
        used.update([a, b, c])
        if backtrack():
            return True
        # backtrack
        solution.pop()
        used.difference_update([a, b, c])
    return False

found = backtrack()
if not found:
    print('WITNESS:', json.dumps({"polarity": "negative", "evidence": {"path": "execution://witness"}, "basis": "search", "search_exhausted": true, "nodes_explored": null, "method": "backtrack"}))
    sys.exit(0)

# Prepare witness data
witness_data = {"triples": solution}
print('WITNESS:', json.dumps({"polarity": "positive", "evidence": {"path": "execution://witness"}, "data": witness_data}))

```json
{
  "files": [
    {
      "filename": "partition_solver.py",
      "satisfies": [
        "R1",
        "R2"
      ],
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "import itertools, sys, json\n\nL = {71, 97, 54, 56, 44, 158, 45, 58, 82, 135, 113, 117, 86, 40, 12, 185, 63, 50, 111, 72, 90, 109, 61, 13, 92, 60, 91, 35, 114, 94, 105, 26, 15, 51, 102, 118, 76, 32, 108, 23, 22, 134, 83, 43, 64}\n\n# Precompute all valid triples (a,b,c) with a<b and a+b=c\ntriples = []\nfor a, b in itertools.combinations(L, 2):\n    s = a + b\n    if s in L:\n        triples.append((a, b, s))\n\n# Build adjacency: for each number, which triples contain it\nfrom collections import defaultdict\nnum_to_triples = defaultdict(list)\nfor idx, t in enumerate(triples):\n    for n in t:\n        num_to_triples[n].append(idx)\n\nsolution = []\nused = set()\n\nsys.setrecursionlimit(10000)\n\ndef backtrack():\n    if len(used) == len(L):\n        return True\n    # choose the unused number with fewest candidate triples (heuristic)\n    candidates = [(n, len([i for i in num_to_triples[n] if all(x not in used for x in triples[i])])) for n in L if n not in used]\n    n, _ = min(candidates, key=lambda x: x[1])\n    for ti in num_to_triples[n]:\n        a, b, c = triples[ti]\n        if a in used or b in used or c in used:\n            continue\n        # select this triple\n        solution.append((a, b, c))\n        used.update([a, b, c])\n        if backtrack():\n            return True\n        # backtrack\n        solution.pop()\n        used.difference_update([a, b, c])\n    return False\n\nfound = backtrack()\nif not found:\n    print('WITNESS:', json.dumps({\"polarity\": \"negative\", \"evidence\": {\"path\": \"execution://witness\"}, \"basis\": \"search\", \"search_exhausted\": true, \"nodes_explored\": null, \"method\": \"backtrack\"}))\n    sys.exit(0)\n\n# Prepare witness data\nwitness_data = {\"triples\": solution}\nprint('WITNESS:', json.dumps({\"polarity\": \"positive\", \"evidence\": {\"path\": \"execution://witness\"}, \"data\": witness_data}))"
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
        "observed": "def backtrack():\n    if len(used) == len(L):\n        return True"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "print('WITNESS:', json.dumps({\"polarity\": \"positive\", \"evidence\": {\"path\": \"execution://witness\"}, \"data\": witness_data}))"
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
