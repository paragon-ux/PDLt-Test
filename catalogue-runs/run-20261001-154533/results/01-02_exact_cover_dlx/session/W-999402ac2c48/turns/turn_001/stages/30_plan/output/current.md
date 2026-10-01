CONSTRUCT the exact cover matrix using rows S1..S9 and columns 1..9.
BUILD dancing‑links structures to represent the matrix.
INITIALIZE an empty collection to hold solutions.
APPLY Algorithm X:
    SELECT a column with the fewest remaining rows.
    CHOOSE a row that covers the selected column.
    COVER the chosen row and all columns it contains.
    RECURSIVELY continue the search.
    IF a complete cover is achieved THEN
        RECORD the current set of chosen rows as a solution.
    UN‑COVER the previously covered rows and columns before backtracking.
VERIFY each recorded solution by confirming that every element of U appears in exactly one selected set.
EMIT the list of exact‑cover subcollections together with the verification routine.
