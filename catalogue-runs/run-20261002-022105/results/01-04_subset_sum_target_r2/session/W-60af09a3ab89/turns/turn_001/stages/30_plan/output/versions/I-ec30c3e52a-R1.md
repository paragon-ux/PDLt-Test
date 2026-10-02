SET S = {3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21}
SET T = 40
USE a backtracking algorithm that explores the full search tree
INITIALIZE solution_count to 0
DEFINE BACKTRACK(remaining_elements, current_subset, current_sum):
    IF current_sum EQUALS T THEN
        EMIT current_subset
        VERIFY current_sum EQUALS T
        INCREMENT solution_count
    ENDIF
    IF current_sum GREATER THAN T THEN
        RETURN
    ENDIF
    FOR EACH element IN remaining_elements DO
        CALL BACKTRACK(remaining_elements MINUS element, current_subset UNION element, current_sum PLUS element)
    ENDFOR
CALL BACKTRACK(S, EMPTY_SET, 0)
REPORT solution_count
