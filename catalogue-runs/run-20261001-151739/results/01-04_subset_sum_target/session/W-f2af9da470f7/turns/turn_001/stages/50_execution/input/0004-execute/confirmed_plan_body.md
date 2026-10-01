PARSE the supplied set S and target T
INITIALIZE a backtracking search over the elements of S
RECURSIVELY EXPLORE inclusion and exclusion of each element to build candidate subsets
    IF the running sum equals T
        EMIT the current subset
        VERIFY that the emitted subset sums to T
        INCREMENT the solution counter
    ENDIF
CONTINUE exploring remaining branches to exhaust the full search tree
AFTER completing the search, REPORT the total number of solutions found
