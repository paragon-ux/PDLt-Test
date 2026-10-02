READ the 7x7 Latin square where zeros denote empty cells
INITIALIZE candidate value sets for each empty cell
WHILE there exist unfilled cells
    PROPAGATE constraints to reduce candidate values
    IF any cell has no candidates
        BACKTRACK to previous assignment
    ELSE
        SELECT a cell with the fewest candidates
        ASSIGN a candidate value to the selected cell
ENDWHILE
VERIFY that each row is a permutation of {1,…,7}
VERIFY that each column is a permutation of {1,…,7}
EMIT the completed square and verification results
