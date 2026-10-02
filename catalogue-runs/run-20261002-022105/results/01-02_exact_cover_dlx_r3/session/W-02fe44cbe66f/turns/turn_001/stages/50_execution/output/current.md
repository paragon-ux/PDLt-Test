import json
from typing import List, Dict, Set

# Define universe and subsets
U = {1, 2, 3, 4, 5, 6, 7, 8, 9}
subsets = {
    'S1': {1, 2, 3},
    'S2': {4, 5, 6},
    'S3': {7, 8, 9},
    'S4': {1, 4, 7},
    'S5': {2, 5, 8},
    'S6': {3, 6, 9},
    'S7': {1, 5, 9},
    'S8': {2, 6, 7},
    'S9': {3, 4, 8},
}

# Build the exact cover matrix: rows -> subset name, columns -> elements of U
# Represent as dict[row] = set(columns it covers)
matrix: Dict[str, Set[int]] = {name: elems.copy() for name, elems in subsets.items()}

solutions: List[List[str]] = []
nodes_explored = 0

def choose_column(remaining_rows: Set[str]) -> int:
    """Choose the column (element) with the fewest rows covering it (heuristic)."""
    counts: Dict[int, int] = {e: 0 for e in U}
    for r in remaining_rows:
        for e in matrix[r]:
            counts[e] += 1
    # ignore columns already covered (count == 0)
    # pick smallest non‑zero count
    min_count = None
    chosen = None
    for e, c in counts.items():
        if c == 0:
            continue
        if min_count is None or c < min_count:
            min_count = c
            chosen = e
    return chosen

def search(partial: List[str], remaining_rows: Set[str], covered: Set[int]):
    global nodes_explored
    nodes_explored += 1
    if covered == U:
        solutions.append(partial.copy())
        return
    # pick a column to cover next
    col = choose_column(remaining_rows)
    if col is None:
        return
    # rows that cover this column
    rows_with_col = [r for r in remaining_rows if col in matrix[r]]
    for row in rows_with_col:
        # add row to partial solution
        new_partial = partial + [row]
        # rows and columns that are eliminated
        cols_covered = matrix[row]
        new_covered = covered.union(cols_covered)
        # eliminate rows that intersect with these columns
        new_remaining = {r for r in remaining_rows if matrix[r].isdisjoint(cols_covered)}
        search(new_partial, new_remaining, new_covered)

# Start search
search([], set(matrix.keys()), set())

# Verification test
def verify_solution(sol: List[str]) -> bool:
    covered = set()
    for name in sol:
        covered ^= subsets[name]  # XOR to detect duplicate coverage
    return covered == U

assert all(verify_solution(sol) for sol in solutions), "Verification failed"

# Build witness JSON
witness = {
    "polarity": "positive",
    "data": {
        "count": len(solutions),
        "solutions": solutions,
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
      "count": 3,
      "solutions": [
        [
          "S1",
          "S2",
          "S3"
        ],
        [
          "S7",
          "S8",
          "S9"
        ],
        [
          "S4",
          "S5",
          "S6"
        ]
      ]
    },
    "provisional": true
  }
}
```
