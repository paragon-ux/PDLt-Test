READ the list L of 45 distinct positive integers
GENERATE all unordered pairs (a, b) from L where a < b
FILTER pairs where a + b is also in L and distinct from a and b
FORM triples (a, b, c) with c = a + b
SEARCH for a selection of 15 triples that are pairwise disjoint and collectively cover L
IF a valid selection exists THEN
    EMIT an example set of the 15 triples
ELSE
    EMIT a statement that no such partition exists
ENDIF
