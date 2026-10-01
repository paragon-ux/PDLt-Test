def backtrack(start, current, current_sum):
    if current_sum == TARGET:
        solutions.append(current.copy())
        print(current.copy())
        return
    if current_sum > TARGET or start >= len(S):
        return
    for i in range(start, len(S)):
        current.append(S[i])
        backtrack(i+1, current, current_sum + S[i])
        current.pop()

S = [3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21]
TARGET = 40
solutions = []
backtrack(0, [], 0)
print('TOTAL SOLUTIONS:', len(solutions))
import json
witness = {
    'polarity': 'positive',
    'data': {
        'solutions': solutions,
        'total_solutions': len(solutions)
    }
}
print('WITNESS: ' + json.dumps(witness))

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
