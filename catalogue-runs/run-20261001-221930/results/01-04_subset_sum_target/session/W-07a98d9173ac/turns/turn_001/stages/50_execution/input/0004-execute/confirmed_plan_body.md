USE backtracking algorithm that explores the full search tree
LOAD the set S and the target T
INITIALIZE solution counter to zero
DEFINE BACKTRACK(index, subset, sum):
    IF sum equals T THEN EMIT subset; VERIFY sum equals T; INCREMENT solution counter
    IF sum > T OR index >= length of S THEN RETURN
    CALL BACKTRACK(index + 1, subset with S[index] added, sum + S[index])
    CALL BACKTRACK(index + 1, subset, sum)
CALL BACKTRACK(0, empty set, 0)
REPORT solution counter
