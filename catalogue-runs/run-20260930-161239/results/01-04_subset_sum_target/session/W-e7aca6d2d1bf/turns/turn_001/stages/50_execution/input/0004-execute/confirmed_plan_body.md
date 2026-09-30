READ the set S and the target T
EXECUTE a backtracking search that explores the full search tree of subsets of S
FOR each node, TRACK the current subset and its cumulative sum
IF the cumulative sum equals T THEN
EMIT the current subset
VERIFY that the subset sum equals T
ELSE IF the cumulative sum exceeds T OR all elements have been considered THEN
BACKTRACK to explore alternative subsets
CONTINUE until the entire search tree has been exhausted
AFTER enumeration completes, REPORT the total number of solutions
