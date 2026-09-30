READ the set S and target value T
INITIALIZE solution_counter to 0
DEFINE BACKTRACK(current_subset, start_index, current_sum)
IF current_sum EQUALS T THEN
OUTPUT current_subset as a solution
INCREMENT solution_counter
ELSE IF current_sum GREATER THAN T THEN
RETURN
ENDIF
FOR each index i FROM start_index TO LENGTH of S MINUS 1 DO
ADD S[i] TO current_subset
CALL BACKTRACK WITH (current_subset, i PLUS 1, current_sum PLUS S[i])
REMOVE last element FROM current_subset
ENDFOR
ENDDEFINE
CALL BACKTRACK WITH (empty subset, 0, 0)
OUTPUT solution_counter as the total number of solutions
