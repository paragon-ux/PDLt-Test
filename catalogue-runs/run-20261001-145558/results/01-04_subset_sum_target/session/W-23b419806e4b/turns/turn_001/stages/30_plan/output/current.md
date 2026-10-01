READ the set S
READ the target value T
INITIALIZE a counter for solutions to zero
EXECUTE a backtracking search to explore all subsets of S
FOR each generated subset
    IF the subset sum equals T
        EMIT the subset
        INCREMENT the solution counter
    ENDIF
ENDFOR
REPORT the total number of solutions
