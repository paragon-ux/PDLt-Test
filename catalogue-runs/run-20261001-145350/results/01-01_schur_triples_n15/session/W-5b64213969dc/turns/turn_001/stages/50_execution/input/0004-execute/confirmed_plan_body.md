READ the list L of 45 distinct positive integers
GENERATE all possible triples (a, b, c) from L such that a + b = c
BUILD a combinatorial search structure to select 15 disjoint triples covering every element of L exactly once
SEARCH for a set of 15 disjoint triples that satisfies the coverage constraint
IF a valid partition is found THEN EMIT one complete example of the 15 triples
ELSE EMIT a statement that no such partition exists
