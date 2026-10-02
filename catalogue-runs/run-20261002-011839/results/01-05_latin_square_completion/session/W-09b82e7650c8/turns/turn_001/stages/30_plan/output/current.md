PARSE the provided partially filled 7x7 Latin square
APPLY constraint propagation to deduce possible values for empty cells
INITIATE backtracking search to assign numbers to empty cells while maintaining Latin square constraints
ON each assignment, PROPAGATE constraints to prune infeasible options
IF a conflict arises, BACKTRACK to previous assignment and try alternative value
CONTINUE until all cells are filled satisfying row and column uniqueness
VERIFY that every row contains a permutation of {1,2,3,4,5,6,7}
VERIFY that every column contains a permutation of {1,2,3,4,5,6,7}
EMIT the completed Latin square
