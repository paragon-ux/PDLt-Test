import itertools, json

S = [3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21]
T = 40
solutions = []
# Explore all subsets via backtracking
def backtrack(idx, current, current_sum):
    if current_sum == T:
        solutions.append(list(current))
        return
    if idx >= len(S) or current_sum > T:
        return
    # include S[idx]
    current.append(S[idx])
    backtrack(idx + 1, current, current_sum + S[idx])
    current.pop()
    # exclude S[idx]
    backtrack(idx + 1, current, current_sum)

backtrack(0, [], 0)
# Verify each solution sums to T
for sol in solutions:
    assert sum(sol) == T
# Emit subsets and total count
for sol in solutions:
    print(sol)
print("TOTAL SOLUTIONS:", len(solutions))
# Witness output
witness = {
    "polarity": "positive",
    "data": {
        "solutions": solutions,
        "total": len(solutions)
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
      "total": 19
    },
    "provisional": false
  }
}
```
