READ the list L of 45 distinct positive integers
GENERATE all possible triples (a, b, c) from L such that a + b = c
BUILD a graph or hypergraph representation where each integer is a node and each valid triple is a hyper‑edge connecting three nodes
APPLY a combinatorial search or exact cover algorithm (e.g., Algorithm X with dancing links) to select 15 disjoint hyper‑edges that cover every node exactly once
IF a complete exact‑cover solution is found THEN
FORMAT the selected 15 triples as the required partition output
ELSE
REPORT that no valid partition exists
ENDIF
