READ the partially filled 7x7 Latin square containing zeros as empty cells
PROPAGATE constraints to reduce possible values for each empty cell
APPLY BACKTRACKING search to assign numbers where propagation alone is insufficient
VERIFY that each row contains a permutation of {1,2,3,4,5,6,7}
VERIFY that each column contains a permutation of {1,2,3,4,5,6,7}
EMIT the completed square
