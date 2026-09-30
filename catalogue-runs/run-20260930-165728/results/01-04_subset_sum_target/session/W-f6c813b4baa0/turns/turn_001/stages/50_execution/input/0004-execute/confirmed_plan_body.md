BACKTRACK through the set S to generate all possible subsets
FOR each generated subset
IF the subset sum equals T
EMIT the subset
VERIFY that the sum of the emitted subset equals T
INCREMENT a solution counter
ENDIF
ENDFOR
REPORT the total number of solutions found
