READ the list of 45 distinct positive integers
GENERATE all unordered triples (a, b, c) from the list such that a + b = c
BUILD a graph where each integer is a node and each valid triple is a hyper‑edge connecting three nodes
SEARCH for a set of 15 disjoint hyper‑edges that together cover every node exactly once (e.g., via backtracking or exact‑cover algorithm)
IF a covering set of 15 triples is found THEN PREPARE an output listing each triple
ELSE PREPARE a statement that no such partition exists
