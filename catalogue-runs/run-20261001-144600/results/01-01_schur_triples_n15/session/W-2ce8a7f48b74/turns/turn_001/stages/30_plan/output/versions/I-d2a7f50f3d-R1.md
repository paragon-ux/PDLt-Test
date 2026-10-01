PARSE the supplied list of 45 distinct positive integers
GENERATE all possible unordered triples (a, b, c) from the list where a + b = c
BUILD a graph where each integer is a node and each valid triple is a hyperedge connecting three nodes
SEARCH for a set of 15 disjoint hyperedges that cover all 45 nodes using a backtracking algorithm or exact cover solver
IF such a partition is found THEN
    SELECT one solution set of 15 triples
    FORMAT each triple as (a, b, c) and LIST them sequentially
ELSE
    REPORT that no valid partition exists
