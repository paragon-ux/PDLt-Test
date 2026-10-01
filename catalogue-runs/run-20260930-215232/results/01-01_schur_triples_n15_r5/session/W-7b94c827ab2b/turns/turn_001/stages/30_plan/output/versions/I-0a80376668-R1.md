READ the set L and the declared number of elements
NOTE the target number of triples (15)
DECLARE placeholders a_i, b_i, c_i for each i in 1..15
REQUIRE a_i + b_i = c_i for each i
SEARCH for a partition of L into 15 disjoint triples (a_i, b_i, c_i)
FOR each candidate partition
    VALIDATE that each triple satisfies a_i + b_i = c_i
    IF all triples satisfy the constraint
        EMIT one complete example of the 15 triples
        EXIT
IF no valid partition is found
    EMIT that no valid partition exists
