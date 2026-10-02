READ the list L of 45 distinct positive integers
DETERMINE whether L can be partitioned into 15 disjoint triples (a_i, b_i, c_i) such that a_i + b_i = c_i for each triple
IF a valid partition exists THEN
    CONSTRUCT one example partition satisfying the condition
    OUTPUT the example partition
ELSE
    OUTPUT a statement that no such partition exists
READ the universe U = {1,2,3,4,5,6,7,8,9} and the collection of sets S1‑S9
APPLY Knuth's Algorithm X with dancing‑links to enumerate all exact covers of U
OUTPUT each exact cover as a list of set identifiers
PERFORM a self‑contained test that verifies each reported solution covers every element of U exactly once
