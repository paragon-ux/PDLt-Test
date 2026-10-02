READ the list L of 45 distinct positive integers
DEFINE N as 15
INITIALIZE an empty collection of triples
FOR each unordered combination of three distinct integers from L
    IF the sum of the first two equals the third AND none of the three integers appear in any previously selected triple
        ADD the triple to the collection
    ENDIF
ENDFOR
IF the collection contains exactly N triples
    FORMAT and RETURN the collection of triples
ELSE
    RETURN a statement that no valid partition exists
ENDIF
