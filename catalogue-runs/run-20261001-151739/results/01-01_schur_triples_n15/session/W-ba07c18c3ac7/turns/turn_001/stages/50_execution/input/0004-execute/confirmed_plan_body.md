READ the list L of 45 numbers
GENERATE all candidate triples (a, b, c) where a + b = c and a, b, c are distinct elements of L
FILTER the candidate triples to ensure each element of L appears at most once per triple
APPLY an exact‑cover search to select a subset of 15 triples that together cover all 45 elements without overlap
IF a covering subset is found
    EMIT the selected 15 triples
ELSE
    EMIT a statement that no valid partition exists
