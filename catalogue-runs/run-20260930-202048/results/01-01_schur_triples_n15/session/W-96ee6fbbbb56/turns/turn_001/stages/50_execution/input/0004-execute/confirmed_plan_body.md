VERIFY that the supplied list contains exactly 45 distinct positive integers
GENERATE all possible ordered pairs (a, b) from the list where a < b
FOR each pair, COMPUTE c = a + b and CHECK if c is present in the list and distinct from a and b
BUILD a graph where each integer is a node and each valid triple (a, b, c) forms a hyperedge linking three nodes
APPLY a backtracking search to SELECT 15 disjoint hyperedges that cover all 45 nodes without overlap
IF a complete set of 15 disjoint triples is found THEN
    PREPARE the list of triples as the required example
ELSE
    REPORT that no such partition exists
