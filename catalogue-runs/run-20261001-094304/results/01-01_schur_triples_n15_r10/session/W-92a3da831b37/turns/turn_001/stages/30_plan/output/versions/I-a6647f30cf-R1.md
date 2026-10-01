PARSE the provided list L of integers and the integer N.
GENERATE the set of all possible triples (a, b, c) from L such that a + b = c.
BUILD a representation linking each integer to the triples that contain it.
SEARCH for a collection of N triples that are pairwise disjoint and together cover all elements of L.
VERIFY that the found collection indeed covers every element of L exactly once.
IF a valid collection is found THEN
    FORMAT the collection as an ordered list of N triples.
    OUTPUT the formatted partition.
ELSE
    FORMAT a statement indicating that no partition exists.
    OUTPUT the statement.
ENDIF
