PARSE the provided 7x7 Latin square
INITIALIZE each empty cell (marked 0) with domain {1,...,7}
APPLY constraint propagation to reduce domains based on row and column constraints
WHILE there exist unassigned cells
    SELECT an unassigned cell with the smallest domain
    IF the selected cell has an empty domain THEN
        BACKTRACK to previous decision point
    ELSE
        ASSIGN a value from its domain to the cell
        APPLY constraint propagation to update affected cells
    ENDIF
ENDWHILE
IF all cells are assigned THEN
    EMIT the completed grid
    VERIFY that each row is a permutation of {1,...,7}
    VERIFY that each column is a permutation of {1,...,7}
ENDIF
