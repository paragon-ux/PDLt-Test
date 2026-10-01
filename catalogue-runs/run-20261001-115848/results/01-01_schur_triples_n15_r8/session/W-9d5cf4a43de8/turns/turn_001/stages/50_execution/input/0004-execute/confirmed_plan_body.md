PARSE the input list L and integer N
GENERATE candidate triples (a, b, c) where a, b, c ∈ L, a < b, and a + b = c
BUILD a covering structure where each candidate triple covers its three elements
SEARCH for a set of N disjoint triples that exactly covers all elements of L
IF a covering set of N triples is found THEN
    OUTPUT one such set of triples as the example partition
ELSE
    REPORT that no valid partition exists
