PARSE the supplied list of integers into a collection L.
GENERATE all unordered triples (a, b, c) from L such that a + b = c and a, b, c are distinct.
BUILD a search for a selection of 15 triples from the generated set that are pairwise disjoint and together cover all 45 elements of L.
IF a disjoint triple cover is found,
    EMIT the selected 15 triples as the required example partition.
ELSE
    EMIT a statement that no partition meeting the condition exists.
