READ the list L and integer N
VALIDATE that |L| = 3 * N and all elements are distinct
GENERATE candidate triples (a,b,c) from L where a + b = c and a, b, c are distinct
BUILD a selection model to choose triples such that each element of L appears in at most one chosen triple
SEARCH for a set of N triples that satisfy the disjointness and coverage constraints
IF a valid set of N triples is found THEN
    EMIT the set of triples as the partition
ELSE
    EMIT a statement that no valid partition exists
