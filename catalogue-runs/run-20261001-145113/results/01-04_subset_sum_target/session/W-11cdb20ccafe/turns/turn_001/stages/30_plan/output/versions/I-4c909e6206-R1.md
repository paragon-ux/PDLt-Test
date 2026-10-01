INITIATE an empty collection SOLUTIONS and a COUNTER set to 0
DEFINE BACKTRACK(subset, sum, start_index) AS a routine that EXPLORES the full search tree of subsets of S
  IF sum = 40 THEN
    EMIT subset
    VERIFY sum = 40
    INCREMENT COUNTER
  ELSE IF sum > 40 OR start_index >= size of S THEN
    RETURN
  ELSE
    FOR i FROM start_index TO size of S - 1 DO
      ADD S[i] TO subset
      CALL BACKTRACK(subset, sum + S[i], i + 1)
      REMOVE S[i] FROM subset
CALL BACKTRACK with empty subset, sum 0, start_index 0
REPORT COUNTER as the total number of solutions
