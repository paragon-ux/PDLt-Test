import json

# Partially filled 7x7 Latin square (0 denotes empty)
initial_square = [
    [1, 0, 0, 0, 5, 6, 7],
    [0, 0, 0, 0, 0, 0, 0],
    [3, 0, 0, 0, 7, 0, 2],
    [4, 0, 0, 7, 0, 0, 0],
    [5, 6, 7, 1, 0, 3, 0],
    [0, 7, 1, 2, 0, 4, 0],
    [0, 0, 0, 0, 0, 0, 6],
]
N = 7
ALL = set(range(1, N + 1))

def is_valid(square):
    # Verify rows
    for r, row in enumerate(square):
        if set(row) != ALL:
            return False
    # Verify columns
    for c in range(N):
        col = {square[r][c] for r in range(N)}
        if col != ALL:
            return False
    return True

def find_empty(square):
    for r in range(N):
        for c in range(N):
            if square[r][c] == 0:
                return r, c
    return None

def possible_values(square, row, col):
    used = set(square[row]) | {square[r][col] for r in range(N)}
    return ALL - used

def solve(square):
    # Constraint propagation: fill cells with a single possibility repeatedly
    progress = True
    while progress:
        progress = False
        for r in range(N):
            for c in range(N):
                if square[r][c] == 0:
                    opts = possible_values(square, r, c)
                    if len(opts) == 1:
                        square[r][c] = opts.pop()
                        progress = True
    # Backtracking if not solved
    empty = find_empty(square)
    if not empty:
        return square
    r, c = empty
    for val in possible_values(square, r, c):
        new_sq = [row[:] for row in square]
        new_sq[r][c] = val
        result = solve(new_sq)
        if result is not None:
            return result
    return None

solution = solve([row[:] for row in initial_square])
if solution is None:
    raise RuntimeError("No solution found")

# Verify solution
assert is_valid(solution), "Verification failed"

print("Completed Latin square:")
for row in solution:
    print(row)

# Emit witness for the host
witness = {
    "polarity": "positive",
    "evidence": {"path": "execution://witness"},
    "data": {"solution": solution}
}
print("WITNESS:", json.dumps(witness))

```json
{
  "files": [
    {
      "filename": "solver.py",
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
        "observed": "# Partially filled 7x7 Latin square (0 denotes empty)\\ninitial_square = [...]"
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
        "observed": "# Partially filled 7x7 Latin square (0 denotes empty)"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "def solve(square):"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "assert is_valid(solution), \\\"Verification failed\\\""
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "assert is_valid(solution)"
      }
    },
    {
      "requirement": "R5",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "print(\\\"Completed Latin square:\\\")"
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
      "solution": [
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
    "provisional": false
  }
}
```
