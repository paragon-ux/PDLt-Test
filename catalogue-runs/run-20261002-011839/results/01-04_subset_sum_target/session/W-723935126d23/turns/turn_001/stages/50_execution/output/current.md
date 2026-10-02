import json

def find_subsets(nums, target):
    results = []
    subset = []
    def backtrack(start, current_sum):
        if current_sum == target:
            results.append(list(subset))
            return
        if current_sum > target or start == len(nums):
            return
        for i in range(start, len(nums)):
            subset.append(nums[i])
            backtrack(i + 1, current_sum + nums[i])
            subset.pop()
    backtrack(0, 0)
    return results

S = [3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21]
T = 40
solutions = find_subsets(S, T)
# Verify each solution's sum (should be 40)
verified = []
for sol in solutions:
    total = sum(sol)
    if total == T:
        verified.append(sol)
# Prepare witness
witness = {
    "polarity": "positive",
    "data": {
        "solutions": verified,
        "total_solutions": len(verified)
    }
}
print("WITNESS: " + json.dumps(witness))

```json
{
  "files": [],
  "reconciliation": [],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
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
