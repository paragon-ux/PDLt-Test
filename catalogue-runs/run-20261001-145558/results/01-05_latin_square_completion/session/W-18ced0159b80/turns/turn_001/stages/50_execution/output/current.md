import json

def solve_latin_square():
    # Initial grid with 0 as empty
    grid = [
        [1, 0, 0, 0, 5, 6, 7],
        [0, 0, 0, 0, 0, 0, 0],
        [3, 0, 0, 0, 7, 0, 2],
        [4, 0, 0, 7, 0, 0, 0],
        [5, 6, 7, 1, 0, 3, 0],
        [0, 7, 1, 2, 0, 4, 0],
        [0, 0, 0, 0, 0, 0, 6],
    ]
    n = 7
    # Precompute possible values for each cell
    possibilities = [[set(range(1, n+1)) if grid[r][c]==0 else {grid[r][c]} for c in range(n)] for r in range(n)]

    def propagate():
        changed = True
        while changed:
            changed = False
            for r in range(n):
                for c in range(n):
                    if grid[r][c] != 0:
                        continue
                    # eliminate values already used in row and column
                    row_vals = {grid[r][j] for j in range(n) if grid[r][j] != 0}
                    col_vals = {grid[i][c] for i in range(n) if grid[i][c] != 0}
                    allowed = possibilities[r][c] - row_vals - col_vals
                    if not allowed:
                        return False
                    if allowed != possibilities[r][c]:
                        possibilities[r][c] = allowed
                        changed = True
                    if len(allowed) == 1:
                        val = allowed.pop()
                        grid[r][c] = val
                        possibilities[r][c] = {val}
                        changed = True
        return True

    def backtrack():
        # find empty cell with fewest possibilities
        min_len = n+1
        cell = None
        for r in range(n):
            for c in range(n):
                if grid[r][c] == 0:
                    l = len(possibilities[r][c])
                    if l < min_len:
                        min_len = l
                        cell = (r, c)
        if cell is None:
            return True  # solved
        r, c = cell
        saved_grid = [row[:] for row in grid]
        saved_poss = [[s.copy() for s in row] for row in possibilities]
        for val in list(possibilities[r][c]):
            grid[r][c] = val
            possibilities[r][c] = {val}
            if propagate() and backtrack():
                return True
            # restore
            grid[:] = [row[:] for row in saved_grid]
            possibilities[:] = [[s.copy() for s in row] for row in saved_poss]
        return False

    if not propagate():
        return None
    if backtrack():
        return grid
    return None

solution = solve_latin_square()
if solution is None:
    witness = {"polarity": "negative", "basis": "search", "search_exhausted": True, "nodes_explored": None, "method": "backtracking"}
else:
    witness = {"polarity": "positive", "data": {"solution": solution}}
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
          4,
          3,
          5,
          6,
          7
        ],
        [
          2,
          3,
          5,
          6,
          4,
          7,
          1
        ],
        [
          3,
          1,
          6,
          4,
          7,
          5,
          2
        ],
        [
          4,
          5,
          2,
          7,
          6,
          1,
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
          7,
          4,
          3,
          5,
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
