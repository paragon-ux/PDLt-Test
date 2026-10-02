READ the list L (45 distinct positive integers)
VALIDATE that L contains exactly 45 distinct positive integers
COMPUTE N = 15
GENERATE all unordered pairs (a, b) from L where a < b
FOR each pair (a, b) DO
    CALCULATE sum = a + b
    IF sum is present in L AND sum is distinct from a and b THEN
        RECORD candidate triple (a, b, sum)
    ENDIF
ENDFOR
FORMULATE the set of candidate triples as an exact-cover problem
APPLY an exact-cover solver to select 15 disjoint triples covering all elements of L
IF a solution is found THEN
    OUTPUT one complete example of the partition, listing each triple (a_i, b_i, c_i)
ELSE
    OUTPUT that no valid partition exists
ENDIF
