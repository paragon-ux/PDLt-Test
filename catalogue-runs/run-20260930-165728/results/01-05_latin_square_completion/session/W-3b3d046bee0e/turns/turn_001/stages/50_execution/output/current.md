import sys, json

def solve_latin_square(board):
    N = 7
    rows = [set(r) - {0} for r in board]
    cols = [set(board[r][c] for r in range(N)) - {0} for c in range(N)]
    def possible(r, c):
        return set(range(1, N+1)) - rows[r] - cols[c]
    def backtrack():
        # find empty cell with fewest possibilities
        min_opts = None
        min_pos = None
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    opts = possible(r, c)
                    if not opts:
                        return False
                    if min_opts is None or len(opts) < len(min_opts):
                        min_opts = opts
                        min_pos = (r, c)
        if min_opts is None:
            return True  # solved
        r, c = min_pos
        for val in sorted(min_opts):
            board[r][c] = val
            rows[r].add(val)
            cols[c].add(val)
            if backtrack():
                return True
            board[r][c] = 0
            rows[r].remove(val)
            cols[c].remove(val)
        return False
    if not backtrack():
        raise ValueError("No solution found")
    return board

def main():
    input_board = [
        [1, 0, 0, 0, 5, 6, 7],
        [0, 0, 0, 0, 0, 0, 0],
        [3, 0, 0, 0, 7, 0, 2],
        [4, 0, 0, 7, 0, 0, 0],
        [5, 6, 7, 1, 0, 3, 0],
        [0, 7, 1, 2, 0, 4, 0],
        [0, 0, 0, 0, 0, 0, 6],
    ]
    solution = solve_latin_square(input_board)
    # Verify rows and columns
    N = 7
    for r in range(N):
        assert set(solution[r]) == set(range(1, N+1))
    for c in range(N):
        assert set(solution[r][c] for r in range(N)) == set(range(1, N+1))
    print("Completed Latin square:")
    for row in solution:
        print(row)
    witness = {
        "polarity": "positive",
        "evidence": {"path": "execution://witness"},
        "data": {"solution": solution}
    }
    print("WITNESS:" + json.dumps(witness))

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
        "section": "",
        "observed": "import sys, json"
      }
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "input_board = [...]"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "def solve_latin_square(board):"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "assert set(solution[r]) == set(range(1, N+1))"
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "assert set(solution[r][c] for r in range(N)) == set(range(1, N+1))"
      }
    },
    {
      "requirement": "R5",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
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
