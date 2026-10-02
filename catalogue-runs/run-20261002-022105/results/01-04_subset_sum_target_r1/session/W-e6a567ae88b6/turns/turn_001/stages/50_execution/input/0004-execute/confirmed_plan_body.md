READ the set S = {3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21}
READ the target value T = 40
INITIALIZE an empty collection for matching subsets
INITIALIZE a counter set to zero
APPLY BACKTRACKING algorithm with parameters (current_subset, start_index, current_sum) that
    IF current_sum equals T THEN
        VERIFY that the sum of current_subset equals T
        EMIT current_subset
        INCREMENT counter
    ENDIF
    IF current_sum > T OR start_index >= size of S THEN
        RETURN
    ENDIF
    FOR each element i from start_index to size of S - 1 DO
        ADD element i to current_subset
        RECURSE BACKTRACKING with (current_subset, i+1, current_sum + element i)
        REMOVE element i from current_subset
    ENDFOR
REPORT counter as the total number of emitted subsets
