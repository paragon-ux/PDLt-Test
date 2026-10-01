READ the list L of 45 distinct positive integers
GENERATE the set T of all candidate triples (a, b, c) from L such that a + b = c
APPLY a backtracking search to SELECT 15 disjoint triples from T that together cover every element of L exactly once
IF a complete selection is found THEN
    RETURN the 15 selected triples as the partition
ENDIF
