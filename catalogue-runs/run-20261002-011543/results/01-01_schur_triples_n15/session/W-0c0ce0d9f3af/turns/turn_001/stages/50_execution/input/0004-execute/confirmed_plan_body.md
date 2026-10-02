READ the provided list L of 45 distinct positive integers
GENERATE all candidate triples (a, b, c) from L such that a + b = c
BUILD a hypergraph where each candidate triple is an edge linking its three numbers
SEARCH for a set of 15 disjoint edges that together cover all 45 numbers
    IF a covering set is found
        EMIT one complete example of the partition consisting of the 15 triples
    ENDIF
