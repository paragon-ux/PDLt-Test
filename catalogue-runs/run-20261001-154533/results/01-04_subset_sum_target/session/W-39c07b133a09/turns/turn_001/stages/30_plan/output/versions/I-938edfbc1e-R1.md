DEFINE set S = {3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21}
DEFINE target T = 40
INITIALIZE solution counter to 0
DEFINE BACKTRACK(subset, remaining elements, current sum):
    IF current sum equals T THEN
        EMIT subset
        VERIFY current sum equals T
        INCREMENT solution counter
    ENDIF
    IF current sum greater than T THEN
        RETURN
    ENDIF
    FOR each element in remaining elements DO
        CALL BACKTRACK with subset ∪ {element}, remaining elements after element, current sum + element
    ENDFOR
ENDDEFINE
CALL BACKTRACK with empty subset, S, 0
REPORT solution counter as total number of solutions
