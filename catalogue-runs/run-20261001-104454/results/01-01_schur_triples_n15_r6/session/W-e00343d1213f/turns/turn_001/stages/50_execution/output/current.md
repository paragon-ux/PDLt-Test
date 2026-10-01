import json

L = [71, 97, 54, 56, 44, 158, 45, 58, 82, 135, 113, 117, 86, 40, 12, 185, 63, 50, 111, 72, 90, 109, 61, 13, 92, 60, 91, 35, 114, 94, 105, 26, 15, 51, 102, 118, 76, 32, 108, 23, 22, 134, 83, 43, 64]

def find_triples(nums):
    num_set = set(nums)
    triples = []
    for i, a in enumerate(nums):
        for b in nums[i+1:]:
            c = a + b
            if c in num_set:
                triples.append((a, b, c))
    return triples

def build_index(triples):
    idx = {n: [] for n in L}
    for ti, (a, b, c) in enumerate(triples):
        idx[a].append(ti)
        idx[b].append(ti)
        idx[c].append(ti)
    return idx

def backtrack(used, solution):
    if len(used) == len(L):
        return solution
    min_num = None
    min_options = None
    for n in L:
        if n in used:
            continue
        options = [ti for ti in num_to_triples[n] if all(x not in used for x in triples[ti])]
        if not options:
            return None
        if min_options is None or len(options) < len(min_options):
            min_options = options
            min_num = n
            if len(min_options) == 1:
                break
    for ti in min_options:
        a, b, c = triples[ti]
        new_used = used | {a, b, c}
        res = backtrack(new_used, solution + [(a, b, c)])
        if res is not None:
            return res
    return None

triples = find_triples(L)
num_to_triples = build_index(triples)

solution = backtrack(set(), [])
if solution is None:
    witness = {"polarity":"negative","evidence":{"path":"execution://witness"},"basis":"proof","argument":"No partition exists."}
else:
    partition = [list(t) for t in solution]
    witness = {"polarity":"positive","evidence":{"path":"execution://witness"},"data":{"partition":partition}}
print("WITNESS: " + json.dumps(witness))

```json
{
  "files": [
    {
      "filename": "solution.py",
      "satisfies": [
        "R1"
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
