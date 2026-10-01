EXTRACT the provided list L of 45 distinct positive integers
GENERATE all candidate triples (a, b, c) such that a + b = c, using distinct elements of L
CONSTRUCT a set‑cover representation where each candidate triple covers its three elements
APPLY a combinatorial exact‑cover algorithm (e.g., DLX or backtracking) to select 15 disjoint triples that together cover every element of L
IF a valid exact‑cover is found, FORMAT the selected 15 triples for presentation
ELSE, DETERMINE that no such partition exists
