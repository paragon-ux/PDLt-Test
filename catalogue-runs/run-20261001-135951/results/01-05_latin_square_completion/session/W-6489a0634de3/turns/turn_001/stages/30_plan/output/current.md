PARSE the 7x7 Latin square grid with zeros
APPLY constraint propagation to reduce possible values for each zero cell
IF any zero cells remain unresolved THEN PERFORM backtracking search to assign values consistent with Latin square constraints
OUTPUT the completed 7x7 Latin square
VERIFY that each row contains the numbers 1 through 7 exactly once
VERIFY that each column contains the numbers 1 through 7 exactly once
