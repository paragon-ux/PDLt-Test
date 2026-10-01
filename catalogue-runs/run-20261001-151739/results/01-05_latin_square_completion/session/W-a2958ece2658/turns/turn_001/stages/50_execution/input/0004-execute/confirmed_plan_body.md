PARSE the supplied rows into a 7x7 grid representation.
INITIALIZE domain {1,…,7} for each empty cell.
APPLY constraint propagation to reduce domains based on row and column constraints.
IF any cell domain becomes empty THEN
    TERMINATE with failure.
ENDIF
SELECT an empty cell with the smallest domain.
FOR each value in the selected cell's domain DO
    ASSIGN the value to the cell.
    RECURSIVELY invoke the solving procedure (including constraint propagation).
    IF the recursive call succeeds THEN
        RETURN success.
    ENDIF
ENDFOR
BACKTRACK upon failure of all candidates.
WHEN all cells are assigned THEN
    VERIFY that each row and each column is a permutation of {1,…,7}.
    EMIT the completed square.
ENDWHEN
