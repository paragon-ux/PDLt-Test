READ the partially filled 7x7 Latin square grid where zeros represent empty cells
APPLY constraint propagation to eliminate impossible numbers from each empty cell based on Latin square rules
IF further propagation is possible THEN REPEAT propagation
ELSE PERFORM backtracking search to assign numbers to remaining empty cells, ensuring row and column uniqueness
CONTINUE backtracking until the grid is completely filled
VERIFY that the completed grid satisfies the Latin square property for all rows and columns
