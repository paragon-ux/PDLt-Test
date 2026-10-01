READ the partially provided 7x7 Latin square.
APPLY constraint propagation to reduce candidate values for each empty cell.
WHILE unfilled cells remain
    IF any cell has no candidates THEN BACKTRACK to previous assignment.
    ELSE SELECT a cell with multiple candidates and ASSIGN a candidate value.
    ENDIF
    APPLY constraint propagation after assignment.
ENDWHILE
OUTPUT the completed square.
VERIFY that each row contains each number 1 through 7 exactly once.
VERIFY that each column contains each number 1 through 7 exactly once.
