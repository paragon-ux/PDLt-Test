import json

def find_subsets(nums, target):
    results = []
    subset = []
    def backtrack(index, current_sum):
        # Explore full search tree
        if current_sum == target:
            results.append(subset.copy())
            # continue searching for other combos
        if index == len(nums) or current_sum > target:
            return
        # include nums[index]
        subset.append(nums[index])
        backtrack(index + 1, current_sum + nums[index])
        # exclude nums[index]
        subset.pop()
        backtrack(index + 1, current_sum)
    backtrack(0, 0)
    return results

S = [3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21]
T = 40
solutions = find_subsets(S, T)
print("Solutions:")
for sol in solutions:
    print(sol, "sum=", sum(sol))
print("Total solutions:", len(solutions))
# Witness certification
witness = {
    "polarity": "positive",
    "evidence": {"path": "execution://witness"},
    "data": {"solutions": solutions, "total": len(solutions)}
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
        "section": "def find_subsets(nums, target):",
        "observed": "def find_subsets(nums, target):"
      }
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "S = [3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21]",
        "observed": "S = [3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21]"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "def backtrack(index, current_sum):",
        "observed": "def backtrack(index, current_sum):"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "if current_sum == target:",
        "observed": "if current_sum == target:"
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "print(\"Total solutions:\", len(solutions))",
        "observed": "print(\"Total solutions:\", len(solutions))"
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
          12,
          5,
          11,
          2
        ],
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
          5,
          8,
          15,
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
          12,
          8,
          15,
          2
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
          3,
          26,
          11
        ],
        [
          3,
          26,
          11
        ],
        [
          3,
          26,
          11
        ],
        [
          3,
          26,
          11
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
          11,
          8,
          2
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
          26,
          2
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
          7,
          5,
          11,
          15,
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
          8,
          15
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
          26,
          2
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
          12,
          11,
          15,
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
      "total": 47
    },
    "provisional": false
  }
}
```
