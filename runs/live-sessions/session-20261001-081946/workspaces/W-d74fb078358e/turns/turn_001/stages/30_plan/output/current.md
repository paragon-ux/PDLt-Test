GENERATE all possible triples (a, b, c) from the supplied list L such that a + b = c
BUILD a hypergraph where each triple is a hyperedge covering its three elements
APPLY an exact‑cover algorithm (e.g., Algorithm X with dancing links) to select 15 disjoint triples that cover all 45 numbers
IF a solution is found THEN FORMAT the selected triples as (a_i, b_i, c_i) for i = 1..15
ELSE REPORT that no valid partition exists
