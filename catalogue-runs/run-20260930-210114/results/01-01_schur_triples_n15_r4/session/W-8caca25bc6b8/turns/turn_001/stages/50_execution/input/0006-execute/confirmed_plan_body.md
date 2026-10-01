VALIDATE that the input list contains 45 distinct positive integers
GENERATE all possible ordered pairs (a, b) from the list where a < b
FOR each pair, CHECK if the sum a + b exists in the list as a distinct element c
IF such c exists, RECORD the triple (a, b, c) as a candidate
BUILD a collection of candidate triples ensuring no element appears in more than one triple within a candidate set
SEARCH for a set of 15 candidate triples that together cover all 45 integers exactly once (an exact‑cover problem)
IF a complete exact‑cover set is found, PREPARE the 15 triples as the required example
ELSE, REPORT that no such partition exists
