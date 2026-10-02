READ the provided 7x7 Latin square with empty cells marked as 0
INITIALIZE a constraint matrix representing possible values for each cell
APPLY constraint propagation to reduce possibilities based on row and column constraints
IF any cell has no possible values THEN
    BACKTRACK to previous assignment
ENDIF
WHILE there exist empty cells
    SELECT an empty cell with the fewest possible values
    CHOOSE a candidate value for the selected cell
    ASSIGN the chosen value
    APPLY constraint propagation to update possibilities
    IF a contradiction arises THEN
        REVERT the assignment and BACKTRACK
    ENDIF
ENDWHILE
OUTPUT the completed Latin square
VERIFY that every row is a permutation of the set {1,2,3,4,5,6,7}
VERIFY that every column is a permutation of the set {1,2,3,4,5,6,7}
