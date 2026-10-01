DEFINE S as {3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21}
DEFINE T as 40
INITIALIZE solution_count to 0
CALL BACKTRACK with empty subset and full S
IN BACKTRACK(current_subset, remaining_elements):
    CALCULATE subset_sum as sum of elements in current_subset
    IF subset_sum equals T THEN
        EMIT current_subset
        INCREMENT solution_count
    ELSE IF subset_sum greater than T THEN
        RETURN
    END IF
    FOR each element e IN remaining_elements DO
        CALL BACKTRACK with current_subset + e and elements after e
    ENDFOR
END BACKTRACK
AFTER BACKTRACK completes:
    REPORT solution_count
