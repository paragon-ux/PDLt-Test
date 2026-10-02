DEFINE the universe U = {1,2,3,4,5,6,7,8,9}
DEFINE the sets S1 through S9 with their specified elements
BUILD an exact‑cover incidence matrix mapping each element of U to each set Si
INITIALIZE a dancing‑links structure from the incidence matrix
SEARCH for all exact‑cover selections using Algorithm X operating on the dancing‑links structure
FOR each selection produced by the search
    COLLECT the identifiers of the sets included in the selection
    VERIFY that the union of the selected sets equals U
    VERIFY that the selected sets are pairwise disjoint
    EMIT the verified selection as an enumerated exact cover
PROVIDE a self‑contained test that iterates over the emitted exact covers and asserts the verification conditions for each
