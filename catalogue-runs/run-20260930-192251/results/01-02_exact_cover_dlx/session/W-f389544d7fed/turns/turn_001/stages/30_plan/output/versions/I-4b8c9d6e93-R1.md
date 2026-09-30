PARSE the definition of universe U and the collection of sets S1 through S9
INITIALIZE the dancing‑links data structures representing the exact‑cover matrix for the sets
IMPLEMENT Algorithm X using the dancing‑links structures to recursively search for exact covers
FOR each recursive branch, SELECT a column (element of U) with the fewest remaining rows
COVER the selected column and all rows containing that element using dancing‑links operations
RECURSE until all columns are covered, then RECORD the current set of rows as an exact‑cover solution
UNCOVER columns when backtracking to explore alternative branches
AFTER the search completes, COLLECT all recorded exact‑cover solutions
GENERATE a self‑contained test that iterates over each recorded solution and VERIFIES that the union of its sets equals U and that each element of U appears exactly once in the solution
OUTPUT the set of exact‑cover solutions and the verification test
