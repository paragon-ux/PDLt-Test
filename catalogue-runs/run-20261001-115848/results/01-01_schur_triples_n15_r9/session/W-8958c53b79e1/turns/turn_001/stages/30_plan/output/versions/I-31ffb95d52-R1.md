VERIFY that L contains 45 distinct positive integers
SET N = 15
GENERATE all unordered pairs (a, b) FROM L
FOR each pair (a, b) DO
  COMPUTE s = a + b
  IF s IN L AND s != a AND s != b THEN
    ADD triple (a, b, s) TO candidate set
  ENDIF
ENDFOR
BUILD a collection of all recorded candidate triples
SEARCH for a subset of exactly N triples that are pairwise disjoint and together cover all elements of L
IF such a subset exists THEN
  OUTPUT the selected triples
ELSE
  OUTPUT that no valid partition exists
ENDIF
