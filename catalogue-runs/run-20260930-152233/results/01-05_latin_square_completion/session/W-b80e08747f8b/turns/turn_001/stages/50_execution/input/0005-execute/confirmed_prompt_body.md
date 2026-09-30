READ the partially completed 7x7 Latin square input
APPLY constraint propagation to enforce that each row contains the numbers 1 through 7 exactly once
APPLY constraint propagation to enforce that each column contains the numbers 1 through 7 exactly once
USE backtracking to explore assignments when propagation alone cannot determine a cell
WHEN a complete assignment is reached, OUTPUT the completed 7x7 Latin square
VERIFY that every row is a permutation of {1,2,3,4,5,6,7}
VERIFY that every column is a permutation of {1,2,3,4,5,6,7}
