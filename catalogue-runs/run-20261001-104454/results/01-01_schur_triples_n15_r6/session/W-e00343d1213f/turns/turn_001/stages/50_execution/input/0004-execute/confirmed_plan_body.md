READ the supplied list of 45 distinct positive integers
GENERATE all possible ordered pairs (a, b) from the list where a < b
IDENTIFY candidate triples (a, b, c) such that a + b = c and c is also in the list
BUILD a constraint graph linking each integer to the triples in which it appears
APPLY a backtracking search to select 15 disjoint triples that cover every integer exactly once
IF a complete set of 15 disjoint triples is found THEN
    FORMAT each selected triple on a separate line for output
ELSE
    REPORT that no valid partition exists
