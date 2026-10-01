PARSE the set S = {3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21} and target T = 40
INITIALIZE an empty list to collect qualifying subsets
DEFINE a BACKTRACK procedure that takes a current subset and remaining elements
    IF the sum of the current subset equals T THEN
        EMIT the current subset
        INCREMENT the count of solutions
    ELSE IF the sum exceeds T THEN
        RETURN
    ENDIF
    FOR each element in the remaining elements
        RECURSIVELY invoke BACKTRACK with the element added to the current subset and the subsequent elements as the new remaining set
    ENDFOR
INVOKE the BACKTRACK procedure with an empty subset and the full list of elements
AFTER enumeration completes, REPORT the total number of solutions
