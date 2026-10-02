INITIALIZE the grid with the given rows:
- Row 1: [1, 0, 0, 0, 5, 6, 7]
- Row 2: [0, 0, 0, 0, 0, 0, 0]
- Row 3: [3, 0, 0, 0, 7, 0, 2]
- Row 4: [4, 0, 0, 7, 0, 0, 0]
- Row 5: [5, 6, 7, 1, 0, 3, 0]
- Row 6: [0, 7, 1, 2, 0, 4, 0]
- Row 7: [0, 0, 0, 0, 0, 0, 6]
APPLY constraint‑propagation to reduce possible values for each zero entry
USE backtracking search to explore assignments when propagation does not yield a single value
CONTINUE propagation and backtracking until all cells are filled
VERIFY that every row and every column is a permutation of {1,…,7}
EMIT the completed Latin square
