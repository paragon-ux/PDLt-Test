PARSE the given list L of 45 distinct positive integers
GENERATE all possible ordered pairs (a, b) from L and compute their sum s = a + b
FILTER the pairs where s is also an element of L, forming candidate triples (a, b, s)
BUILD a search structure mapping each integer to the triples that contain it
APPLY a backtracking algorithm to select 15 disjoint triples such that each integer in L appears exactly once
IF the backtracking succeeds, EXTRACT the selected triples as the required partition
ELSE DETERMINE that no valid partition exists
