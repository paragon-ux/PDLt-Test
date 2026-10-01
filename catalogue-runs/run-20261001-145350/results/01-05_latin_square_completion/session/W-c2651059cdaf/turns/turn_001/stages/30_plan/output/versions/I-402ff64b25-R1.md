READ the 7x7 Latin square puzzle with empty cells marked as 0
INITIALIZE a data structure to represent the grid and possible values for each cell
APPLY constraint propagation to eliminate values that violate row and column uniqueness
WHILE there are unsolved cells DO
    SELECT an unsolved cell with the fewest possible values
    FOR each possible value DO
        ASSIGN the value to the cell
        RECURSIVELY invoke constraint propagation
        IF the grid satisfies all constraints THEN
            RETURN the completed grid
        ENDIF
        REVERT the assignment (backtrack)
    ENDFOR
ENDWHILE
VERIFY that every row and every column is a permutation of {1,…,7}
OUTPUT the completed 7x7 square
