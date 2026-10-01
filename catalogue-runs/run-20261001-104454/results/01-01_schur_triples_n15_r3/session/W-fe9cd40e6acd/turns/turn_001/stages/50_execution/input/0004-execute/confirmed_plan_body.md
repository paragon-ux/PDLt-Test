READ the list L of 45 distinct positive integers
GENERATE all possible triples (a, b, c) from L where a + b = c
BUILD a graph representation linking each integer to the triples in which it appears
APPLY a combinatorial search to select 15 disjoint triples that cover every integer exactly once
IF a valid selection is found THEN OUTPUT the 15 triples
ELSE REPORT that no such partition exists
