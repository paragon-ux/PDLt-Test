GENERATE all possible triples (a, b, c) from the list L where a + b = c
BUILD a graph representation linking numbers to triples they can belong to
APPLY a backtracking search to select 15 disjoint triples covering all 45 numbers
IF a complete covering set is found THEN OUTPUT the selected triples as the partition
ELSE REPORT that no valid partition exists
