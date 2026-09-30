CONSTRUCT a constraint‑propagation model for the 7×7 Latin square with variables for each empty cell and domains {1,…,7}
APPLY backtracking search using the model, propagating constraints to enforce that each row and column contains no duplicate numbers
WHEN a complete assignment is found, VERIFY that every row and column is a permutation of {1,2,3,4,5,6,7}
EMIT the completed Latin square
