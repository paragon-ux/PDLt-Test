READ the initial 7x7 Latin square grid
INITIALIZE a constraint model with variables for each empty cell and domain {1,2,3,4,5,6,7}
APPLY constraint propagation to prune variable domains based on row and column uniqueness constraints
IF any variable domain becomes empty THEN
    BACKTRACK to previous assignment
ENDIF
IF all variables are assigned THEN
    EMIT the completed Latin square
ELSE
    SELECT an unassigned variable with the smallest domain
    FOR each value in the selected variable's domain DO
        ASSIGN the value to the variable
        RECURSIVELY invoke the solver (backtracking)
        IF a complete solution is found THEN
            EXIT loop
        ENDIF
    ENDFOR
ENDIF
VERIFY each row is a permutation of {1,2,3,4,5,6,7}
VERIFY each column is a permutation of {1,2,3,4,5,6,7}
