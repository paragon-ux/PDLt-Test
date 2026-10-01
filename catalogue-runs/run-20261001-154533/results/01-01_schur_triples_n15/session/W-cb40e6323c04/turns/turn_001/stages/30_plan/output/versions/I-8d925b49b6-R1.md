READ the list L of integers
SET N to 15
GENERATE all candidate triples (a, b, c) from L such that a + b = c
BUILD a collection of these candidate triples
SEARCH for a set of N disjoint triples that together cover all elements of L
IF a valid selection is found THEN
    EMIT one complete example of such a partition
ELSE
    REPORT that no valid partition exists
