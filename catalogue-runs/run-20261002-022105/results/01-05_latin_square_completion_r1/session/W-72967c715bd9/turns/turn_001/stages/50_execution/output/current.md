import json

def solve_latin_square():
    # initial grid with 0 as empty
    grid = [
        [1, 0, 0, 0, 5, 6, 7],
        [0, 0, 0, 0, 0, 0, 0],
        [3, 0, 0, 0, 7, 0, 2],
        [4, 0, 0, 7, 0, 0, 0],
        [5, 6, 7, 1, 0, 3, 0],
        [0, 7, 1, 2, 0, 4, 0],
        [0, 0, 0, 0, 0, 0, 6],
    ]
    N = 7
    # precompute possible values for each cell
    rows = [set() for _ in range(N)]
    cols = [set() for _ in range(N)]
    for r in range(N):
        for c in range(N):
            val = grid[r][c]
            if val != 0:
                rows[r].add(val)
                cols[c].add(val)
    def domain(r, c):
        return set(range(1, N+1)) - rows[r] - cols[c]
    # find empty cells
    empties = [(r, c) for r in range(N) for c in range(N) if grid[r][c] == 0]
    # backtracking with MRV
    def backtrack(index=0):
        if index == len(empties):
            return True
        # select cell with smallest domain
        best_i = None
        best_domain = None
        for i in range(index, len(empties)):
            r, c = empties[i]
            d = domain(r, c)
            if not d:
                return False
            if best_domain is None or len(d) < len(best_domain):
                best_domain = d
                best_i = i
                if len(d) == 1:
                    break
        # swap to current position
        empties[index], empties[best_i] = empties[best_i], empties[index]
        r, c = empties[index]
        for val in best_domain:
            # assign
            grid[r][c] = val
            rows[r].add(val)
            cols[c].add(val)
            if backtrack(index + 1):
                return True
            # revert
            grid[r][c] = 0
            rows[r].remove(val)
            cols[c].remove(val)
        # restore order
        empties[index], empties[best_i] = empties[best_i], empties[index]
        return False
    success = backtrack()
    if not success:
        raise ValueError("No solution found")
    # verify rows and columns are permutations 1..7
    for r in range(N):
        if set(grid[r]) != set(range(1, N+1)):
            raise AssertionError(f"Row {r+1} invalid")
    for c in range(N):
        col = {grid[r][c] for r in range(N)}
        if col != set(range(1, N+1)):
            raise AssertionError(f"Column {c+1} invalid")
    return grid

def main():
    solution = solve_latin_square()
    witness = {
        "polarity": "positive",
        "data": {
            "completed_square": solution
        }
    }
    print("WITNESS: " + json.dumps(witness))

if __name__ == "__main__":
    main()

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
    "provisional": true
  }
}
```
