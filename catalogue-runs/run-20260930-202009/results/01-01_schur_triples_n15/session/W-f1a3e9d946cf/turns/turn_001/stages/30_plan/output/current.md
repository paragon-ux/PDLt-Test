DEFINE the set L of 45 distinct positive integers
GENERATE all possible ordered pairs (a,b) from L where a<b and compute c = a+b
FILTER those triples (a,b,c) where c is also in L and c≠a,b
BUILD a graph representation with numbers as nodes and valid triples as hyperedges
APPLY a backtracking search to select 15 disjoint triples that cover every element of L exactly once
IF a complete covering set of 15 triples is found THEN
    PREPARE the list of selected triples as the example partition
ELSE
    REPORT that no valid partition exists
