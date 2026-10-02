PARSE the universe definition and the set definitions
BUILD the exact cover matrix linking sets to universe elements
INITIALIZE the dancing-links structure for the matrix
APPLY Knuth's Algorithm X with dancing links to search for exact covers
SELECT sets recursively while maintaining that each element appears exactly once
RECORD each complete exact cover found
CONTINUE the search to enumerate all exact covers
VERIFY each recorded solution with a self‑contained test that each universe element is covered exactly once
EMIT the subcollections representing all exact covers
