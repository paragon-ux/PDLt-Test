PARSE the supplied list of 45 distinct positive integers
GENERATE all possible triples (a, b, c) from the list where a + b = c
BUILD a candidate set of triples covering each integer at most once
APPLY a backtracking search to select 15 disjoint triples that use all 45 integers
IF a complete selection of 15 disjoint triples is found THEN
    PREPARE the output listing each triple as (a_i, b_i, c_i)
ELSE
    PREPARE a statement that no valid partition exists
