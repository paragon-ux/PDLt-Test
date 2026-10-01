# subset_sum.py
# Find all subsets of S that sum to target T using backtracking.

S = [3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21]
T = 40

solutions = []

def backtrack(index, current, total):
    if total == T:
        solutions.append(list(current))
        return
    if total > T or index == len(S):
        return
    # Include S[index]
    current.append(S[index])
    backtrack(index + 1, current, total + S[index])
    current.pop()
    # Exclude S[index]
    backtrack(index + 1, current, total)

backtrack(0, [], 0)

# Emit solutions and verify their sums
for sol in solutions:
    print(f"Subset: {sol}, Sum: {sum(sol)}")
print(f"Total number of solutions: {len(solutions)}")

# Witness output
import json
witness = {
    "polarity": "positive",
    "evidence": {"path": "execution://witness"},
    "data": {
        "solutions": solutions,
        "total": len(solutions)
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
        "observed": "# subset_sum.py\n# Find all subsets of S that sum to target T using backtracking."
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
        "observed": "def backtrack(index, current, total):\\n    if total == T:\\n        solutions.append(list(current))\\n        return"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "for sol in solutions:\\n    print(f\\\"Subset: {sol}, Sum: {sum(sol)}\\\")"
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "print(f\\\"Total number of solutions: {len(solutions)}\\\")"
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
      "total": 19
    },
    "provisional": false
  }
}
```
