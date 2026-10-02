READ the universe definition U = {1, 2, 3, 4, 5, 6, 7, 8, 9}
READ the set definitions S1 = {1, 2, 3}
READ the set definitions S2 = {4, 5, 6}
READ the set definitions S3 = {7, 8, 9}
READ the set definitions S4 = {1, 4, 7}
READ the set definitions S5 = {2, 5, 8}
READ the set definitions S6 = {3, 6, 9}
READ the set definitions S7 = {1, 5, 9}
READ the set definitions S8 = {2, 6, 7}
READ the set definitions S9 = {3, 4, 8}
BUILD an exact cover matrix with rows for each set and columns for each element of U
IMPLEMENT Knuth's Algorithm X using dancing links to manipulate the matrix
EXECUTE the Algorithm X search to enumerate all exact cover solutions
COLLECT each solution as a set of selected subsets
VERIFY that each solution covers every element of U exactly once
INCLUDE a test that asserts the verification condition for each enumerated solution
EMIT the self-contained implementation and the verification test
