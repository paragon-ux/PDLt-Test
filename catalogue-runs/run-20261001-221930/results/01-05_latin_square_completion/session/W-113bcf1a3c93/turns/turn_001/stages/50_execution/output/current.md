#!/usr/bin/env python3
import json

def solve_latin_square(grid):
    N = 7
    rows = [set(row) - {0} for row in grid]
    cols = [set(grid[r][c] for r in range(N)) - {0} for c in range(N)]
    empties = [(r, c) for r in range(N) for c in range(N) if grid[r][c] == 0]

    def backtrack(idx=0):
        if idx == len(empties):
            return True
        # choose cell with fewest candidates
        best_i = None
        best_candidates = None
        for i in range(idx, len(empties)):
            r, c = empties[i]
            candidates = set(range(1, N+1)) - rows[r] - cols[c]
            if not candidates:
                return False
            if best_candidates is None or len(candidates) < len(best_candidates):
                best_candidates = candidates
                best_i = i
                if len(best_candidates) == 1:
                    break
        # swap chosen with current idx
        empties[idx], empties[best_i] = empties[best_i], empties[idx]
        r, c = empties[idx]
        for val in best_candidates:
            grid[r][c] = val
            rows[r].add(val)
            cols[c].add(val)
            if backtrack(idx+1):
                return True
            rows[r].remove(val)
            cols[c].remove(val)
            grid[r][c] = 0
        # restore order
        empties[idx], empties[best_i] = empties[best_i], empties[idx]
        return False

    if not backtrack():
        return None
    return grid

# Input Latin square with 0 as empty
initial_grid = [
    [1, 0, 0, 0, 5, 6, 7],
    [0, 0, 0, 0, 0, 0, 0],
    [3, 0, 0, 0, 7, 0, 2],
    [4, 0, 0, 7, 0, 0, 0],
    [5, 6, 7, 1, 0, 3, 0],
    [0, 7, 1, 2, 0, 4, 0],
    [0, 0, 0, 0, 0, 0, 6]
]
solution = solve_latin_square([row[:] for row in initial_grid])
if solution is None:
    witness = {
        "polarity": "negative",
        "basis": "search",
        "search_exhausted": True,
        "nodes_explored": None,
        "method": "backtracking with constraint propagation"
    }
else:
    # verify each row and column is permutation 1..7
    N = 7
    ok = all(set(row) == set(range(1, N+1)) for row in solution) and all(set(solution[r][c] for r in range(N)) == set(range(1, N+1)) for c in range(N))
    if not ok:
        witness = {
            "polarity": "negative",
            "basis": "proof",
            "argument": "Result does not satisfy Latin square constraints"
        }
    else:
        witness = {
            "polarity": "positive",
            "data": {"completed_square": solution}
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
      "completed_square": [
        [
          1,
          2,
          4,
          3,
          5,
          6,
          7
        ],
        [
          7,
          5,
          3,
          6,
          4,
          2,
          1
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
          1,
          2,
          7,
          6,
          5,
          3
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
          2,
          3,
          5,
          4,
          1,
          7,
          6
        ]
      ]
    },
    "provisional": false
  }
}
```
