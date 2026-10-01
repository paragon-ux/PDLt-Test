READ the list L of integers
GENERATE candidate groupings of three distinct elements from L
FILTER groupings to retain only those where the sum of the first two elements equals the third element
SEARCH for a collection of 15 disjoint groupings that together cover all elements of L
IF a complete collection of 15 disjoint valid triples is found THEN
    OUTPUT the 15 triples as the example partition
ELSE
    REPORT that no such partition exists
