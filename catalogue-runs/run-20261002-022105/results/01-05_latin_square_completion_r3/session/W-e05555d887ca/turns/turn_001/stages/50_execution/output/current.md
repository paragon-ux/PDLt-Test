import json
from copy import deepcopy

def solve_latin(square):
    n = len(square)
    # rows and columns used numbers
    row_used = [set() for _ in range(n)]
    col_used = [set() for _ in range(n)]
    empties = []
    for i in range(n):
        for j in range(n):
            val = square[i][j]
            if val != 0:
                row_used[i].add(val)
                col_used[j].add(val)
            else:
                empties.append((i, j))
    def backtrack(idx):
        if idx == len(empties):
            return True
        i, j = empties[idx]
        for v in range(1, n+1):
            if v not in row_used[i] and v not in col_used[j]:
                square[i][j] = v
                row_used[i].add(v)
                col_used[j].add(v)
                if backtrack(idx+1):
                    return True
                # undo
                square[i][j] = 0
                row_used[i].remove(v)
                col_used[j].remove(v)
        return False
    backtrack(0)
    return square

def verify(square):
    n = len(square)
    target = set(range(1, n+1))
    for i in range(n):
        if set(square[i]) != target:
            return False
    for j in range(n):
        col = {square[i][j] for i in range(n)}
        if col != target:
            return False
    return True

partial = [
    [1, 0, 0, 0, 5, 6, 7],
    [0, 0, 0, 0, 0, 0, 0],
    [3, 0, 0, 0, 7, 0, 2],
    [4, 0, 0, 7, 0, 0, 0],
    [5, 6, 7, 1, 0, 3, 0],
    [0, 7, 1, 2, 0, 4, 0],
    [0, 0, 0, 0, 0, 0, 6]
]
solution = solve_latin(deepcopy(partial))
assert verify(solution), "Verification failed"
# Prepare witness
witness = {
    "polarity": "positive",
    "data": {
        "completed_square": solution
    }
}
print("WITNESS: " + json.dumps(witness))

[host] Witness values are written into the program, not computed; unverified.

```json
{
  "files": [],
  "reconciliation": [],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "data": {
      "completed_square": [
        [
          1,
          2,
          3,
          4,
          5,
          6,
          7
        ],
        [
          2,
          1,
          5,
          6,
          4,
          7,
          3
        ],
        [
          3,
          4,
          6,
          5,
          7,
          1,
          2
        ],
        [
          4,
          3,
          2,
          7,
          6,
          5,
          1
        ],
        [
          5,
          6,
          7,
          1,
          2,
          3,
          4
        ],
        [
          6,
          7,
          1,
          2,
          3,
          4,
          5
        ],
        [
          7,
          5,
          4,
          3,
          1,
          2,
          6
        ]
      ]
    },
    "provisional": true
  }
}
```
