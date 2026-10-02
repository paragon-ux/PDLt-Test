PARSE set S and target T = 40
INITIALIZE empty list of solution subsets
DEFINE BACKTRACK(current_subset, current_sum, next_index)
    IF current_sum equals T THEN EMIT current_subset; VERIFY its sum; ADD to solution list
    ELSE IF current_sum > T OR next_index >= SIZE OF S THEN RETURN
    ELSE
        INCLUDE element S[next_index] IN current_subset; INCREMENT current_sum; CALL BACKTRACK with next_index + 1
        EXCLUDE element S[next_index] FROM current_subset; CALL BACKTRACK with next_index + 1
CALL BACKTRACK with empty subset, sum 0, index 0
REPORT total number of solution subsets found
