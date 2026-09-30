READ the partially filled 7x7 Latin square grid input where zeros represent empty cells
APPLY constraint propagation to reduce possible values for each empty cell based on Latin square rules (each number 1-7 must appear exactly once per row and column)
IF any cell has no possible values THEN BACKTRACK to a previous decision and try an alternative value
CONTINUE propagation and backtracking until all zeros are filled
VERIFY that each row and each column contains the numbers 1 through 7 exactly once
EMIT the completed 7x7 Latin square grid as the result
