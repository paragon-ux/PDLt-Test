READ the set S = {3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21}
READ the target T = 40
INITIALIZE an empty collection SOLUTIONS
DEFINE a BACKTRACKING PROCEDURE with parameters CURRENT_SUBSET and REMAINING_SUM
    IF REMAINING_SUM equals 0 THEN
        EMIT CURRENT_SUBSET
        VERIFY that the sum of CURRENT_SUBSET equals T
        ADD CURRENT_SUBSET to SOLUTIONS
    ELSE IF REMAINING_SUM less than 0 THEN
        RETURN
    ELSE
        FOR each ELEMENT in the remaining elements of S not yet considered
            APPEND ELEMENT to CURRENT_SUBSET
            CALL BACKTRACKING PROCEDURE with CURRENT_SUBSET and REMAINING_SUM minus ELEMENT
            REMOVE ELEMENT from CURRENT_SUBSET
        END_FOR
    END_IF
END_PROCEDURE
CALL BACKTRACKING PROCEDURE with an empty CURRENT_SUBSET and REMAINING_SUM set to T
REPORT the total number of subsets stored in SOLUTIONS
