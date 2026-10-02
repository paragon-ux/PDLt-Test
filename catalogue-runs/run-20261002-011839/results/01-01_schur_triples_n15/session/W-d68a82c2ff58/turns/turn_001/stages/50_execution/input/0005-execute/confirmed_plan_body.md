PARSE the input list of 45 distinct positive integers
GENERATE all possible triples (a, b, c) where a + b = c
BUILD a graph representation linking integers to candidate triples
SEARCH for a set of 15 disjoint triples that covers all 45 integers using a backtracking or exact cover algorithm
IF a valid partition is found THEN SELECT one such partition
ELSE DETERMINE that no valid partition exists
