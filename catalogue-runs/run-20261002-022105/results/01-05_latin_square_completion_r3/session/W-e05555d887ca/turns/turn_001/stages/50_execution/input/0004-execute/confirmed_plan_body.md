READ the partially filled 7x7 Latin square
INITIALIZE cell domains with values 1..7 for zero cells
APPLY constraint propagation to enforce row and column uniqueness constraints
IF any cell domain remains ambiguous THEN
    PERFORM backtracking search to assign values consistent with constraints
ENDIF
FILL all zero cells with the determined values
EMIT the completed square
VERIFY that every row is a permutation of {1,...,7}
VERIFY that every column is a permutation of {1,...,7}
