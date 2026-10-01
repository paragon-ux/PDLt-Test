READ the set S and the target T
INIT solution count to 0
DEFINE BACKTRACK(current_subset, start_index, current_sum)
    IF current_sum EQUALS T
        EMIT current_subset
        INCREMENT solution count
    ENDIF
    FOR i FROM start_index TO LENGTH OF S MINUS 1
        IF current_sum PLUS S[i] LESS-OR-EQUAL T
            ADD S[i] TO current_subset
            CALL BACKTRACK WITH current_subset, i PLUS 1, current_sum PLUS S[i]
            REMOVE S[i] FROM current_subset
        ENDIF
    ENDFOR
ENDDEFINE
CALL BACKTRACK WITH EMPTY SUBSET, 0, 0
REPORT solution count
