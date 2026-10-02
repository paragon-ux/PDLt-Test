PARSE the input representation of the 7x7 Latin square
INITIALIZE a candidate set {1,...,7} for each empty cell
APPLY constraint propagation to eliminate numbers already present in the same row or column
WHILE any cell has a single candidate DO
    ASSIGN that candidate to the cell
    UPDATE constraints for related rows and columns
ENDWHILE
IF any empty cells remain THEN
    SELECT an empty cell with the smallest candidate set
    FOR each candidate value in the selected cell DO
        ASSIGN the candidate value
        RECURSIVELY attempt to solve the remaining cells using constraint propagation and backtracking
        IF a complete solution is found THEN
            RETURN the solution
        ENDIF
        UNDO the assignment
    ENDFOR
ENDIF
VERIFY that each row and each column is a permutation of {1,...,7}
OUTPUT the completed Latin square
