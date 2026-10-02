PARSE the supplied list L and the integer N
VERIFY that L contains exactly 3 * N numbers
GENERATE all possible triples (a, b, c) from L such that a + b = c and a, b, c are distinct
SEARCH for a set of N disjoint triples covering every element of L
    SELECT a candidate triple and mark its three elements as used
    RECURSE to find remaining triples among the unused elements
    BACKTRACK if the current selection prevents completing a full partition
IF a full partition of N disjoint triples is discovered
    FORMAT the selected triples as the required example
    RETURN the partition
ELSE
    REPORT that no valid partition exists
