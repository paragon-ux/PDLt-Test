READ the list L of 45 distinct positive integers
GENERATE all candidate triples (a, b, c) from L such that a + b = c
CONSTRUCT a representation (e.g., a hypergraph) that maps each number to the triples it participates in
SEARCH for an exact‑cover selection of 15 disjoint triples that together include every number in L
IF a covering selection is found THEN
   SELECT one valid set of 15 triples
   FORMAT the selected triples for presentation
ELSE
   FORMAT a statement indicating that no such partition exists
