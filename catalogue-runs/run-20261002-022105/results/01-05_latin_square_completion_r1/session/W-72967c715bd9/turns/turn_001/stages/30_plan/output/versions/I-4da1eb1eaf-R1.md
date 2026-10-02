READ the partially filled 7x7 Latin square
CONVERT the input into a matrix representation with cell domains
IDENTIFY empty cells (marked 0)
APPLY constraint propagation to reduce domains using row and column uniqueness constraints
USE backtracking search to assign values to empty cells
WHILE there exist unfilled cells
    IF any cell has a single possible value
        ASSIGN that value to the cell
        APPLY constraint propagation
    ELSE
        SELECT an empty cell with the smallest domain
        FOR each possible value in the selected cell's domain
            ASSIGN the value tentatively
            APPLY constraint propagation
            IF no conflict arises
                CONTINUE solving
            ENDIF
            REVERT the tentative assignment
        ENDFOR
    ENDIF
ENDWHILE
VERIFY each row contains each number 1 through 7 exactly once
VERIFY each column contains each number 1 through 7 exactly once
RETURN the completed 7x7 Latin square
