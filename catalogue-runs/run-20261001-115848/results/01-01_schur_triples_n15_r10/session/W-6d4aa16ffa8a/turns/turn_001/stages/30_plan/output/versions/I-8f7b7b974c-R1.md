READ the list L of 45 distinct positive integers
GENERATE all unordered pairs (a, b) from L
FOR each pair (a, b) COMPUTE sum s = a + b
SELECT triples (a, b, c) where c ∈ L, c = s, and c is distinct from a and b
COLLECT all such candidate triples
SEARCH for a set of 15 candidate triples that are pairwise disjoint and together cover all 45 numbers
IF a valid partition exists THEN
    FORMAT the selected triples as (a_i, b_i, c_i) for i = 1 … 15
    EMIT the formatted partition
ENDIF
