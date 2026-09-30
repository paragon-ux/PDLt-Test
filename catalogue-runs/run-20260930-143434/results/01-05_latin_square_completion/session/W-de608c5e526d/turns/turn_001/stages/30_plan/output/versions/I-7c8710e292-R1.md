READ the 7x7 grid with zeros representing empty cells
APPLY constraint‑propagation to reduce possible values for each empty cell based on Latin square row and column rules
IF any cell has no remaining possible values THEN backtrack to previous decision
ELSE IF all cells are assigned THEN EMIT the completed 7x7 Latin square
ELSE SELECT an unfilled cell with the fewest possible values and ASSIGN one of its candidates, then RECURSE to propagate constraints and continue backtracking
VERIFY that every row and column is a permutation of {1,2,3,4,5,6,7}
