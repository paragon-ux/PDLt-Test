READ the list L of 45 distinct positive integers
GENERATE all possible triples (a, b, c) from L where a + b = c
SELECT a set of 15 disjoint triples that together include every element of L exactly once
IF such a selection exists
    RETURN one complete example of the 15 triples
ELSE
    RETURN a statement that no valid partition exists for the given list
