READ the set S
READ the target value T equal to 40
USE a backtracking algorithm to explore all subsets of S
FOR each subset
    IF the subset sum equals T
        EMIT the subset
        VERIFY the sum
    ENDIF
ENDFOR
COUNT the emitted subsets
REPORT the total number of solutions
