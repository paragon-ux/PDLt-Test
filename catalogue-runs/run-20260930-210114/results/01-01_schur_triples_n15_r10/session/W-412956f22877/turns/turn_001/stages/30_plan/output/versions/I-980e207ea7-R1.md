VALIDATE that the input list L contains 45 distinct positive integers
SORT the list L in ascending order
GENERATE all possible unordered triples (a,b,c) from L where a<b and a+b=c
BUILD a graph representation where each integer is a node and each valid triple is a hyper‑edge connecting three nodes
APPLY a hyper‑graph matching algorithm to select 15 disjoint triples covering all 45 nodes
IF a complete matching of size 15 is found THEN
    EXTRACT the selected triples as the required partition
ELSE
    REPORT that no valid partition exists
