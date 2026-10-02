PARSE the set S and the target T
DEFINE a BACKTRACK procedure with parameters (current_subset, start_index, current_sum)
IF current_sum EQUALS T THEN RECORD current_subset
IF current_sum GREATER THAN T OR start_index GREATER THAN OR EQUAL TO LENGTH of S THEN RETURN
FOR index FROM start_index TO LENGTH of S MINUS ONE
    INCLUDE S[index] IN current_subset
    CALL BACKTRACK with (current_subset, index PLUS ONE, current_sum PLUS S[index])
    REMOVE S[index] FROM current_subset
ENDFOR
INITIATE BACKTRACK with an empty subset, start_index ZERO, and current_sum ZERO
AFTER enumeration, COUNT the recorded subsets
OUTPUT each recorded subset and VERIFY its sum
REPORT the total number of solutions
