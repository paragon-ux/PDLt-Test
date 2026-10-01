import json

def solve_latin_square(grid):
    n = len(grid)
    rows = [set(row) - {0} for row in grid]
    cols = [set(grid[r][c] for r in range(n)) - {0} for c in range(n)]
    empty = [(r, c) for r in range(n) for c in range(n) if grid[r][c] == 0]

    def backtrack(idx=0):
        if idx == len(empty):
            return True
        r, c = empty[idx]
        possible = set(range(1, n + 1)) - rows[r] - cols[c]
        for val in possible:
            grid[r][c] = val
            rows[r].add(val)
            cols[c].add(val)
            if backtrack(idx + 1):
                return True
            rows[r].remove(val)
            cols[c].remove(val)
            grid[r][c] = 0
        return False

    if backtrack():
        return grid
    return None

# Input grid from the prompt
input_grid = [
    [1, 0, 0, 0, 5, 6, 7],
    [0, 0, 0, 0, 0, 0, 0],
    [3, 0, 0, 0, 7, 0, 2],
    [4, 0, 0, 7, 0, 0, 0],
    [5, 6, 7, 1, 0, 3, 0],
    [0, 7, 1, 2, 0, 4, 0],
    [0, 0, 0, 0, 0, 0, 6],
]
solution = solve_latin_square([row[:] for row in input_grid])
if solution is None:
    # No solution found
    witness = {
        "polarity": "negative",
        "basis": "search",
        "search_exhausted": True,
        "nodes_explored": None,
        "method": "backtracking",
        "argument": None,
        "domain": None,
        "provisional": False,
    }
else:
    # Verify rows and columns are permutations of 1..7
    n = 7
    ok = all(set(row) == set(range(1, n+1)) for row in solution) and \
         all(set(solution[r][c] for r in range(n)) == set(range(1, n+1)) for c in range(n))
    if ok:
        witness = {
            "polarity": "positive",
            "data": {"solution": solution},
        }
    else:
        witness = {
            "polarity": "negative",
            "basis": "proof",
            "argument": "Verification failed: rows or columns not proper permutations",
            "provisional": False,
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
