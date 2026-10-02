READ the 7x7 Latin square input containing zeros representing missing entries
PARSE the input into a mutable grid structure
APPLY constraint‑propagation to reduce possible values for each zero cell
IF any cell has no possible values THEN backtrack to previous decision
ELSE IF all cells are assigned THEN VERIFY that each row and each column is a permutation of {1,2,3,4,5,6,7}
IF verification succeeds THEN OUTPUT the completed 7x7 square
