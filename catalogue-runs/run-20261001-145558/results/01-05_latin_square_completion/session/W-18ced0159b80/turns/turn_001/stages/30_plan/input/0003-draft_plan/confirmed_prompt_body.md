READ the partially filled 7x7 Latin square grid where zeros represent empty cells
APPLY constraint propagation to eliminate impossible numbers from each empty cell based on the Latin square rule that each row and each column must contain the numbers 1 through 7 exactly once
WHEN no further propagation is possible, PERFORM backtracking search to assign numbers to remaining empty cells, ensuring that each assignment maintains the row and column uniqueness constraints
CONTINUE the backtracking process until the grid is completely filled with numbers 1 through 7 in every row and column
VERIFY that the completed grid satisfies the Latin square property: each row contains each number 1‑7 exactly once and each column contains each number 1‑7 exactly once
