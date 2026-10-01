EXTRACT the list L and the required number of triples (15) from the prompt.
GENERATE all candidate triples (a, b, c) drawn from L such that a + b = c and the three elements are distinct.
BUILD a representation of the candidate triples, e.g., a hypergraph linking each element of L to the triples that contain it.
APPLY a combinatorial exact‑cover search to select a subset of 15 disjoint triples that together cover every element of L.
IF a covering set of 15 triples is found THEN
    EMIT one complete example of the partition.
ELSE
    EMIT a statement that no such partition exists.
ENDIF
