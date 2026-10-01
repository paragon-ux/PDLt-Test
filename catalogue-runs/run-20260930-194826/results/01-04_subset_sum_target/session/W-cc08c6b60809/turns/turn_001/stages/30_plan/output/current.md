READ the set S
READ the target sum T = 40
INITIATE a backtracking exploration of all possible subsets of S
FOR each generated subset
    IF the sum of the subset equals T
        EMIT the subset
        VERIFY that its sum equals T
    ENDIF
ENDFOR
COUNT the total number of emitted subsets
REPORT the total number of solutions
