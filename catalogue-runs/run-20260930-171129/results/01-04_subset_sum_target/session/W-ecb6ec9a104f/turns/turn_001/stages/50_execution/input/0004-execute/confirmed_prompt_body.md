READ the set S = {3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21}
READ the target value T = 40
INITIALIZE solution_counter to 0
DEFINE a BACKTRACK function that takes (current_subset, start_index, current_sum)
IF current_sum equals T THEN
OUTPUT current_subset as a solution
INCREMENT solution_counter
ELSE IF current_sum greater than T THEN
RETURN
ENDIF
FOR each index i from start_index to length of S - 1 DO
ADD S[i] to current_subset
CALL BACKTRACK with (current_subset, i + 1, current_sum + S[i])
REMOVE last element from current_subset
ENDFOR
ENDDEFINE
CALL BACKTRACK with (empty subset, 0, 0)
OUTPUT the total number of solutions as solution_counter
