VALIDATE the input list L contains 45 distinct positive integers
GENERATE all possible ordered pairs (a, b) from L where a < b
FOR each pair compute sum = a + b
FILTER sums that are also members of L and distinct from a and b
BUILD a graph where each integer is a node and each valid triple (a,b,sum) forms a hyperedge connecting three nodes
APPLY a search algorithm to select 15 disjoint hyperedges that cover all 45 nodes
IF a full cover is found THEN
    PREPARE the result indicating existence = true and INCLUDE the 15 triples as the example partition
ELSE
    PREPARE the result indicating existence = false without example
ENDIF
