BUILD a dancing‑links data structure representing the exact‑cover matrix for the universe U and the set collection S1‑S9.
INITIALIZE an empty list to store found exact‑cover solutions.
CALL Algorithm X recursively:
IF the matrix has no columns remaining THEN
RECORD the current partial solution as a complete exact cover in the solutions list.
ELSE
SELECT a column (e.g., using the smallest column heuristic).
FOR each row that contains a 1 in the selected column DO
CHOOSE the row (add it to the partial solution).
COVER the selected column and all other columns covered by the row (remove corresponding rows and columns via dancing links).
RECURSE to continue the search.
UNCOVER the columns and rows to backtrack.
ENDFOR
ENDIF
AFTER the recursion completes, the solutions list contains every subcollection of sets that exactly covers U.
GENERATE a self‑contained test that iterates over each solution in the list and verifies that:
• every element of U appears in exactly one selected set, and
• no element is missing or duplicated.
OUTPUT the list of exact‑cover solutions and the verification test code.
