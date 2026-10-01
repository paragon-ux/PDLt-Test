import json

L = [71, 97, 54, 56, 44, 158, 45, 58, 82, 135, 113, 117, 86, 40, 12, 185, 63, 50, 111, 72, 90, 109, 61, 13, 92, 60, 91, 35, 114, 94, 105, 26, 15, 51, 102, 118, 76, 32, 108, 23, 22, 134, 83, 43, 64]

def find_partition(numbers):
    nums = set(numbers)
    triples = []
    nlist = numbers
    for i, a in enumerate(nlist):
        for b in nlist[i+1:]:
            c = a + b
            if c in nums:
                triples.append((a, b, c))
    triples_by_num = {n: [] for n in numbers}
    for t in triples:
        a, b, c = t
        triples_by_num[a].append(t)
        triples_by_num[b].append(t)
        triples_by_num[c].append(t)
    def search(remaining):
        if not remaining:
            return []
        best_num = None
        best_cands = None
        for n in remaining:
            cands = [t for t in triples_by_num[n] if set(t).issubset(remaining)]
            if not cands:
                return None
            if best_cands is None or len(cands) < len(best_cands):
                best_num = n
                best_cands = cands
                if len(best_cands) == 1:
                    break
        for t in best_cands:
            new_rem = remaining - set(t)
            sol = search(new_rem)
            if sol is not None:
                return [t] + sol
        return None
    return search(nums)

solution = find_partition(L)
if solution is None:
    witness = {"polarity":"negative","evidence":{"path":"execution://witness"},"basis":"search","search_exhausted":True}
else:
    solution_lists = [list(t) for t in solution]
    witness = {"polarity":"positive","evidence":{"path":"execution://witness"},"data":{"triples":solution_lists}}
print("WITNESS: " + json.dumps(witness, separators=(',', ':')))

```json
{
  "files": [
    {
      "filename": "solution.py",
      "satisfies": [
        "R1",
        "R2",
        "R3",
        "R4",
        "R5"
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
          71,
          26,
          97
        ],
        [
          40,
          43,
          83
        ],
        [
          56,
          61,
          117
        ],
        [
          111,
          23,
          134
        ],
        [
          35,
          51,
          86
        ],
        [
          58,
          60,
          118
        ],
        [
          94,
          15,
          109
        ],
        [
          12,
          90,
          102
        ],
        [
          50,
          64,
          114
        ],
        [
          82,
          76,
          158
        ],
        [
          32,
          22,
          54
        ],
        [
          45,
          63,
          108
        ],
        [
          44,
          91,
          135
        ],
        [
          113,
          72,
          185
        ]
      ]
    },
    "provisional": false
  }
}
```
