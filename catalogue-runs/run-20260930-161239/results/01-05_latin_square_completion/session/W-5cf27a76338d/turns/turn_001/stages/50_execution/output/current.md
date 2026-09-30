import sys
from typing import List, Tuple

def parse_grid() -> List[List[int]]:
    # The input grid is embedded in the script for self‑containment.
    return [
        [1, 0, 0, 0, 5, 6, 7],
        [0, 0, 0, 0, 0, 0, 0],
        [3, 0, 0, 0, 7, 0, 2],
        [4, 0, 0, 7, 0, 0, 0],
        [5, 6, 7, 1, 0, 3, 0],
        [0, 7, 1, 2, 0, 4, 0],
        [0, 0, 0, 0, 0, 0, 6],
    ]

def is_valid(grid: List[List[int]]) -> bool:
    n = len(grid)
    target = set(range(1, n + 1))
    for r in range(n):
        if set(grid[r]) != target:
            return False
    for c in range(n):
        col = {grid[r][c] for r in range(n)}
        if col != target:
            return False
    return True

def solve(grid: List[List[int]]) -> Tuple[bool, List[List[int]]]:
    n = len(grid)
    # Pre‑compute possible values for each cell.
    possibilities = [[set(range(1, n + 1)) if grid[r][c] == 0 else {grid[r][c]} for c in range(n)] for r in range(n)]

    def propagate() -> bool:
        changed = True
        while changed:
            changed = False
            # Row propagation
            for r in range(n):
                used = {grid[r][c] for c in range(n) if grid[r][c] != 0}
                for c in range(n):
                    if grid[r][c] == 0:
                        before = len(possibilities[r][c])
                        possibilities[r][c] -= used
                        if len(possibilities[r][c]) == 0:
                            return False
                        if len(possibilities[r][c]) == 1:
                            val = possibilities[r][c].pop()
                            grid[r][c] = val
                            possibilities[r][c] = {val}
                            changed = True
            # Column propagation
            for c in range(n):
                used = {grid[r][c] for r in range(n) if grid[r][c] != 0}
                for r in range(n):
                    if grid[r][c] == 0:
                        before = len(possibilities[r][c])
                        possibilities[r][c] -= used
                        if len(possibilities[r][c]) == 0:
                            return False
                        if len(possibilities[r][c]) == 1:
                            val = possibilities[r][c].pop()
                            grid[r][c] = val
                            possibilities[r][c] = {val}
                            changed = True
        return True

    def backtrack() -> bool:
        # Find unfilled cell with fewest possibilities
        min_len = n + 1
        target = None
        for r in range(n):
            for c in range(n):
                if grid[r][c] == 0:
                    l = len(possibilities[r][c])
                    if l < min_len:
                        min_len = l
                        target = (r, c)
        if target is None:
            return True  # solved
        r, c = target
        snapshot_grid = [row[:] for row in grid]
        snapshot_poss = [[p.copy() for p in row] for row in possibilities]
        for val in sorted(possibilities[r][c]):
            grid[r][c] = val
            possibilities[r][c] = {val}
            if propagate() and backtrack():
                return True
            # restore
            grid[:] = [row[:] for row in snapshot_grid]
            possibilities[:] = [[p.copy() for p in row] for row in snapshot_poss]
        return False

    if not propagate():
        return False, []
    if backtrack():
        return True, grid
    return False, []

def main():
    grid = parse_grid()
    success, solved = solve(grid)
    if not success:
        print("No solution found.")
        sys.exit(1)
    # Verify rows and columns
    assert is_valid(solved), "Verification failed"
    for row in solved:
        print(row)
    # Witness output
    witness = {"solution": solved}
    import json
    print("WITNESS: " + json.dumps(witness))

if __name__ == "__main__":
    main()

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
        "observed": "import sys\\nfrom typing import List, Tuple\\n\\ndef parse_grid() -> List[List[int]]:\\n    # The input grid is embedded in the script for self‑containment.\\n    return [...]"
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
        "observed": "parse_grid() reads the partially filled 7x7 grid input"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "solve(grid) applies constraint propagation with backtracking"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "is_valid(solved) checks each row is a permutation of {1..7}"
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "is_valid(solved) also checks each column permutation"
      }
    },
    {
      "requirement": "R5",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "for row in solved: print(row) outputs the completed square"
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
