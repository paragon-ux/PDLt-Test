INITIALIZE an empty list for solutions
DEFINE a BACKTRACK function with parameters current_subset, remaining_elements, current_sum
    IF current_sum equals T THEN
        EMIT current_subset
        VERIFY that the sum of current_subset equals T
        ADD current_subset to solutions list
    ELSE IF current_sum exceeds T OR remaining_elements is empty THEN
        RETURN
    ELSE
        FOR each element in remaining_elements DO
            CALL BACKTRACK with current_subset plus element, remaining_elements after this element, current_sum plus element
        ENDFOR
    ENDIF
INVOKE BACKTRACK with empty subset, S, and sum 0
REPORT the total number of subsets in solutions list
