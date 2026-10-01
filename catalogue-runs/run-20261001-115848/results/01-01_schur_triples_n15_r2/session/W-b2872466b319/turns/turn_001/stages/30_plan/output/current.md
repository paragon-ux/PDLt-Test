PARSE the input list of integers
COMPUTE all possible unordered pairs (a, b) and their sums c
FILTER candidate triples (a, b, c) where c is in the list and a, b, c are distinct
SEARCH for a collection of 15 disjoint triples covering all 45 numbers such that each triple satisfies a + b = c
IF a valid collection is found THEN
EMIT one example of the valid partition
ELSE
EMIT a statement that no such partition exists
ENDIF
