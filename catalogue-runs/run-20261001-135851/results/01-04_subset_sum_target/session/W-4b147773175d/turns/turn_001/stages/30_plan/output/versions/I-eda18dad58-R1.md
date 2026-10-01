READ the set S and the target value T
INITIALIZE solution count to 0
DEFINE recursive BACKTRACK(current_subset, remaining_elements, current_sum)
    IF current_sum EQUALS T THEN EMIT current_subset AND INCREMENT solution count
    ELSE IF current_sum GREATER THAN T OR remaining_elements IS EMPTY THEN RETURN
    FOR EACH element e IN remaining_elements
        CALL BACKTRACK with current_subset PLUS e, remaining_elements AFTER e, current_sum PLUS e
        CALL BACKTRACK with current_subset unchanged, remaining_elements AFTER e, current_sum
ENDDEFINE
CALL BACKTRACK with empty subset, S, 0
REPORT the total number of solutions
