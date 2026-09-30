import json
S = [3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21]
T = 40
solutions = []

def backtrack(idx, current, total):
    if total == T:
        solutions.append(list(current))
        return
    if total > T or idx == len(S):
        return
    # include element
    current.append(S[idx])
    backtrack(idx + 1, current, total + S[idx])
    current.pop()
    # exclude element
    backtrack(idx + 1, current, total)

backtrack(0, [], 0)
print("Solutions:", solutions)
print("Total:", len(solutions))
witness = {"polarity": "positive", "evidence": {"path": "execution://witness"}, "data": {"solutions": solutions, "count": len(solutions)}}
print("WITNESS:", json.dumps(witness))

```json
{
  "files": [
    {
      "filename": "subset_sum.py",
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
        "observed": "solutions = []"
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
        "observed": "S = [3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21]"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "T = 40"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "backtrack(0, [], 0)"
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "print(\\\"Solutions:\\\", solutions)\"}} ,{",
        "status": "satisfied",
        "evidence": {
          "path": "execution://body",
          "observed": "print(\\\"Total:\\\", len(solutions))"
        }
      },
      "open_defects": []
    }
  ],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "evidence": {
      "path": "execution://witness"
    },
    "data": {
      "solutions": [
        [
          3,
          7,
          12,
          5,
          11,
          2
        ],
        [
          3,
          7,
          5,
          8,
          15,
          2
        ],
        [
          3,
          7,
          11,
          19
        ],
        [
          3,
          12,
          8,
          15,
          2
        ],
        [
          3,
          5,
          11,
          2,
          19
        ],
        [
          3,
          5,
          11,
          21
        ],
        [
          3,
          26,
          11
        ],
        [
          7,
          12,
          11,
          8,
          2
        ],
        [
          7,
          12,
          2,
          19
        ],
        [
          7,
          12,
          21
        ],
        [
          7,
          5,
          26,
          2
        ],
        [
          7,
          5,
          11,
          15,
          2
        ],
        [
          12,
          5,
          8,
          15
        ],
        [
          12,
          5,
          2,
          21
        ],
        [
          12,
          26,
          2
        ],
        [
          12,
          11,
          15,
          2
        ],
        [
          11,
          8,
          2,
          19
        ],
        [
          11,
          8,
          21
        ],
        [
          19,
          21
        ]
      ],
      "count": 19
    },
    "provisional": false
  }
}
```
