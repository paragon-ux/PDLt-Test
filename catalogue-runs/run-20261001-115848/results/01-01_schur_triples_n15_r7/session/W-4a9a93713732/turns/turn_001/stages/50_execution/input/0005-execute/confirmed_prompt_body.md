READ the set L of 45 distinct positive integers
VERIFY that L contains 45 distinct elements
SET N=15
SEARCH for a partition of L into N disjoint triples (a_i, b_i, c_i) such that a_i + b_i = c_i for each triple
IF a valid partition exists THEN
    RETURN one such partition listing each triple as (a_i, b_i, c_i)
ELSE
    RETURN a statement that no such partition exists
