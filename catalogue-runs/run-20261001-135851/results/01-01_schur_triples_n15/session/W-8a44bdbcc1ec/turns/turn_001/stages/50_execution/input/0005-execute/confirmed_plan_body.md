READ the list of 45 distinct positive integers
GENERATE all possible unordered pairs (a, b) from the list where a ≠ b
FOR each pair compute the sum s = a + b
CHECK if s is present in the list and distinct from a and b
CREATE a collection of candidate triples (a, b, c) where a + b = c
CONSTRUCT a representation linking numbers to candidate triples
SEARCH for a set of 15 disjoint triples that cover all 45 numbers using a suitable combinatorial selection method
IF a complete partition exists THEN
OUTPUT the 15 triples as (a, b, c)
ENDIF
