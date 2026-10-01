READ the set L
GENERATE candidate triples (a, b, c) from L where a + b = c
SELECT a collection of 15 disjoint triples that together cover every element of L
IF a valid collection of 15 disjoint triples is found THEN
   EMIT the example list of the 15 triples
ELSE
   EMIT a statement that no such partition exists
