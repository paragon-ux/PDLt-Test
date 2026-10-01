import json

def solve_latin_square():
    N = 7
    # initial grid from prompt
    grid = [
        [1, 0, 0, 0, 5, 6, 7],
        [0, 0, 0, 0, 0, 0, 0],
        [3, 0, 0, 0, 7, 0, 2],
        [4, 0, 0, 7, 0, 0, 0],
        [5, 6, 7, 1, 0, 3, 0],
        [0, 7, 1, 2, 0, 4, 0],
        [0, 0, 0, 0, 0, 0, 6],
    ]

    # precompute row/col used numbers
    rows_used = [set([v for v in row if v != 0]) for row in grid]
    cols_used = [set([grid[r][c] for r in range(N) if grid[r][c] != 0]) for c in range(N)]

    def find_empty():
        # MRV heuristic: cell with smallest domain
        best = None
        best_options = None
        for r in range(N):
            for c in range(N):
                if grid[r][c] == 0:
                    domain = set(range(1, N+1)) - rows_used[r] - cols_used[c]
                    if not domain:
                        return None, None  # dead end
                    if best is None or len(domain) < len(best_options):
                        best = (r, c)
                        best_options = domain
                        if len(best_options) == 1:
                            return best, best_options
        return best, best_options

    def backtrack():
        pos, domain = find_empty()
        if pos is None:
            # either solved or dead end
            if all(all(cell != 0 for cell in row) for row in grid):
                return True
            return False
        r, c = pos
        for val in sorted(domain):
            # place value
            grid[r][c] = val
            rows_used[r].add(val)
            cols_used[c].add(val)
            if backtrack():
                return True
            # undo
            grid[r][c] = 0
            rows_used[r].remove(val)
            cols_used[c].remove(val)
        return False

    success = backtrack()
    if not success:
        raise ValueError("No solution found")
    return grid


def verify(grid):
    N = 7
    expected = set(range(1, N+1))
    for i, row in enumerate(grid):
        if set(row) != expected:
            return False, f"Row {i+1} invalid"
    for c in range(N):
        col = [grid[r][c] for r in range(N)]
        if set(col) != expected:
            return False, f"Column {c+1} invalid"
    return True, "All rows and columns are valid permutations"


def main():
    solution = solve_latin_square()
    ok, message = verify(solution)
    witness = {
        "polarity": "positive",
        "data": {
            "solution": solution,
            "verification": message
        }
    }
    print("WITNESS: " + json.dumps(witness))

if __name__ == "__main__":
    main()

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
      ],
      "verification": "All rows and columns are valid permutations"
    },
    "provisional": false
  }
}
```
