READ the partially filled 7x7 Latin square data
APPLY constraint propagation to reduce possible values for each empty cell
IF any cell has a single possible value THEN assign that value
REPEAT until no further reductions are possible
IF the square is not yet complete THEN BACKTRACK by selecting a cell with the fewest possibilities, assign one possibility, and recurse
VERIFY that each row contains the numbers 1 through 7 exactly once
VERIFY that each column contains the numbers 1 through 7 exactly once
OUTPUT the completed Latin square
