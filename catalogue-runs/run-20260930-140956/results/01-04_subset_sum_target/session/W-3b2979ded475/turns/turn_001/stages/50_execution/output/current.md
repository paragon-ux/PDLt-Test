import itertools, json

S = [3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21]
T = 40
solutions = []
# backtracking explores full search tree
def backtrack(index, current, current_sum):
    if current_sum == T:
        solutions.append(list(current))
        return
    if index >= len(S) or current_sum > T:
        return
    # include S[index]
    current.append(S[index])
    backtrack(index + 1, current, current_sum + S[index])
    current.pop()
    # exclude S[index]
    backtrack(index + 1, current, current_sum)

backtrack(0, [], 0)
print("Subsets summing to", T, ":")
for sol in solutions:
    print(sol)
print("Total solutions:", len(solutions))
# Emit witness line for the host
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
      "filename": "subset_sum_backtrack.py",
      "satisfies": [
        "R1",
        "R2",
        "R3"
      ],
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "import itertools, json\\n\\nS = [3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21]\\nT = 40\\nsolutions = []\\n# backtracking explores full search tree\\ndef backtrack(index, current, current_sum):\\n    if current_sum == T:\\n        solutions.append(list(current))\\n        return\\n    if index >= len(S) or current_sum > T:\\n        return\\n    # include S[index]\\n    current.append(S[index])\\n    backtrack(index + 1, current, current_sum + S[index])\\n    current.pop()\\n    # exclude S[index]\\n    backtrack(index + 1, current, current_sum)\\n\\nbacktrack(0, [], 0)\\nprint(\\\"Subsets summing to\\\", T, \\\" :\\\")\\nfor sol in solutions:\\n    print(sol)\\nprint(\\\"Total solutions:\\\", len(solutions))\\n# Emit witness line for the host\\nwitness = {\\n    \\\"polarity\\\": \\\"positive\\\",\\n    \\\"evidence\\\": {\\\"path\\\": \\\"execution://witness\\\"},\\n    \\\"data\\\": {\\n        \\\"solutions\\\": solutions,\\n        \\\"total\\\": len(solutions)\\n    }\\n}\\nprint(\\\"WITNESS: \\\" + json.dumps(witness))"
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
        "observed": "# backtracking explores full search tree"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "if current_sum == T:\\n        solutions.append(list(current))"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "print(\\\"Total solutions:\\\", len(solutions))"
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
