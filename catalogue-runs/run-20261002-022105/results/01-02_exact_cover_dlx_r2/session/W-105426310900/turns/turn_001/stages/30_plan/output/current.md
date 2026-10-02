READ the universe U and sets S1 through S9
BUILD the exact‑cover matrix representing subsets S1–S9 over elements of U
IMPLEMENT Knuth's Algorithm X using dancing links data structures
EXECUTE Algorithm X to enumerate all exact covers of U
FOR each exact cover found
  GENERATE a self‑contained verification test that checks each element of U appears exactly once in the cover
  ADD the exact cover and its verification test to the result collection
EMIT the list of exact covers together with their associated verification tests
