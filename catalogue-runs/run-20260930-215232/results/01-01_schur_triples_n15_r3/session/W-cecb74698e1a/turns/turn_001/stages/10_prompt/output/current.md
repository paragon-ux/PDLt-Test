READ the list L = {71, 97, 54, 56, 44, 158, 45, 58, 82, 135, 113, 117, 86, 40, 12, 185, 63, 50, 111, 72, 90, 109, 61, 13, 92, 60, 91, 35, 114, 94, 105, 26, 15, 51, 102, 118, 76, 32, 108, 23, 22, 134, 83, 43, 64}
NOTE that L contains 45 distinct positive integers
SET N=15
PARTITION the elements of L into 15 disjoint triples (a_i, b_i, c_i) such that a_i + b_i = c_i for each i from 1 to 15
IF a valid partition exists THEN
    OUTPUT one complete example of the 15 triples
ELSE
    OUTPUT that no such partition exists
ENDIF
