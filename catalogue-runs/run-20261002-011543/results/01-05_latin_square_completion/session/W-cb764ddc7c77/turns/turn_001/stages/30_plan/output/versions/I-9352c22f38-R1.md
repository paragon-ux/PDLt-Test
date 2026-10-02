PARSE the supplied 7x7 grid with zeros representing empty cells
INITIALIZE a domain of possible numbers {1,2,3,4,5,6,7} for each empty cell
APPLY constraint propagation to eliminate numbers already present in the same row or column from each cell's domain
IF any cell's domain becomes empty THEN backtrack to the previous assignment
SELECT an unfilled cell with the smallest domain size
FOR each candidate number in the selected cell's domain DO
    ASSIGN the candidate to the cell
    RECURSIVELY invoke the solver with the updated grid and domains
    IF the recursive invocation succeeds THEN propagate success upward
    ELSE undo the assignment and continue with the next candidate
END_FOR
WHEN all cells are assigned THEN VERIFY that each row and each column is a permutation of {1,2,3,4,5,6,7}
EMIT the completed 7x7 Latin square
