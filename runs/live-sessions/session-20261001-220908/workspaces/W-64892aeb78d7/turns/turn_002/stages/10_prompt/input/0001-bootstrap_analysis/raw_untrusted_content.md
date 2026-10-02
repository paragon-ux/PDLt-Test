Given the list L of 45 distinct positive integers (N=15):
L = {71, 97, 54, 56, 44, 158, 45, 58, 82, 135, 113, 117, 86, 40, 12, 185, 63, 50, 111, 72, 90, 109, 61, 13, 92, 60, 91, 35, 114, 94, 105, 26, 15, 51, 102, 118, 76, 32, 108, 23, 22, 134, 83, 43, 64}

Determine whether L can be partitioned into 15 disjoint triples (a_i, b_i, c_i) such that a_i + b_i = c_i for every triple i in {1, ..., 15}. If a valid partition exists, emit one complete example.

Follow-up from the user, referring to the request above:
Given the universe U = {1, 2, 3, 4, 5, 6, 7, 8, 9} and the collection of sets:
S1 = {1, 2, 3}, S2 = {4, 5, 6}, S3 = {7, 8, 9},
S4 = {1, 4, 7}, S5 = {2, 5, 8}, S6 = {3, 6, 9},
S7 = {1, 5, 9}, S8 = {2, 6, 7}, S9 = {3, 4, 8}

Find ALL exact covers of U (subcollections where every element of U appears in exactly one selected set). Implement the search using Knuth's Algorithm X with dancing links. Include a self-contained test that verifies each solution covers U exactly once.
