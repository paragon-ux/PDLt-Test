LOAD the given set L of integers
GENERATE all candidate triples (a, b, c) from L where a + b = c
FILTER candidate triples to keep only those with distinct elements
SEARCH for a collection of 15 disjoint triples that together cover every element of L using backtracking or constraint solving
IF a complete covering is found THEN OUTPUT the 15 triples as the partition
ELSE OUTPUT a statement that no valid partition exists
