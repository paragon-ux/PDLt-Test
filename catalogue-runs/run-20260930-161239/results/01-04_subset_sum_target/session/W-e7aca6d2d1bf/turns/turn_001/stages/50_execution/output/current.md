# Backtracking search for subsets of S that sum to T
S = [3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21]
T = 40
solutions = []

def backtrack(index, current, total):
    if total == T:
        solutions.append(list(current))
        return
    if total > T or index == len(S):
        return
    # include S[index]
    current.append(S[index])
    backtrack(index + 1, current, total + S[index])
    current.pop()
    # exclude S[index]
    backtrack(index + 1, current, total)

backtrack(0, [], 0)
# Verify each solution sum equals T
for sol in solutions:
    assert sum(sol) == T
# Report total number of solutions
total_solutions = len(solutions)
# Output witness for verification
import json, sys
witness = {
    "polarity": "positive",
    "evidence": {"path": "execution://witness"},
    "data": {
        "solutions": solutions,
        "total_solutions": total_solutions
    }
}
print("WITNESS: " + json.dumps(witness))

```json
{
  "files": [
    {
      "filename": "subset_sum.py",
      "satisfies": [
        "R1",
        "R2",
        "R3",
        "R4"
      ],
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "# Backtracking search for subsets of S that sum to T"
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
        "observed": "S = [3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21]\\nT = 40"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "def backtrack(index, current, total):\\n    if total == T:\\n        solutions.append(list(current))\\n        return\\n    if total > T or index == len(S):\\n        return\\n    current.append(S[index])\\n    backtrack(index + 1, current, total + S[index])\\n    current.pop()\\n    backtrack(index + 1, current, total)"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "for sol in solutions:\\n    assert sum(sol) == T"
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "total_solutions = len(solutions)"
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
      "total_solutions": 19
    },
    "provisional": false
  }
}
```
