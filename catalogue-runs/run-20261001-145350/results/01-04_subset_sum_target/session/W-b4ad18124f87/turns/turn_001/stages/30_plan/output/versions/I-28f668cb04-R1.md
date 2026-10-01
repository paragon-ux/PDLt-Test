READ the set S and the target value T
INITIALIZE an empty collection to store found subsets
DEFINE a BACKTRACK procedure with parameters (position, current_subset, current_sum)
    IF current_sum EQUALS T THEN
        EMIT current_subset
        VERIFY that the sum of current_subset equals T
        ADD current_subset to the collection of solutions
        RETURN
    ENDIF
    IF position GREATER THAN OR EQUAL TO the size of S OR current_sum GREATER THAN T THEN
        RETURN
    ENDIF
    // Explore branch including the element at the current position
    CALL BACKTRACK with (position + 1, current_subset UNION {S[position]}, current_sum + S[position])
    // Explore branch excluding the element at the current position
    CALL BACKTRACK with (position + 1, current_subset, current_sum)
ENDDEFINE
CALL BACKTRACK starting at position 0 with an empty subset and sum 0
AFTER completing the search, REPORT the total number of solutions stored in the collection
