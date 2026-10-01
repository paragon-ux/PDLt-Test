READ the list L and the integer N
GENERATE all candidate triples (a,b,c) from L where a + b = c
BUILD a tracking structure to ensure each element is used at most once
SEARCH for a collection of N disjoint triples that together use all elements of L
IF a valid partition is found THEN
    OUTPUT the 15 triples
ELSE
    OUTPUT that no such partition exists
ENDIF
