READ the list L and the integer N
VALIDATE that N is 15 and that the size of L equals 3 * N
SEARCH for a partition of L into N disjoint triples (a, b, c) satisfying a + b = c
IF a valid partition is found THEN
    SELECT one such partition
    EMIT the selected triples
ELSE
    EMIT a statement that no such partition exists
