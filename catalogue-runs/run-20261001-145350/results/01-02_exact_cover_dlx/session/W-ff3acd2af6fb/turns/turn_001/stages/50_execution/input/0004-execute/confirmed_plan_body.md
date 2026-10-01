PARSE the universe set U and the collection of sets S1 through S9
BUILD a dancing‑links data structure representing the exact‑cover matrix for U and S1‑S9
EXECUTE Algorithm X using the dancing‑links structure to enumerate all exact covers of U
FOR each enumeration result, RECORD the subset of sets that constitutes a solution
VALIDATE each recorded solution by checking that every element of U appears exactly once across the chosen sets
GENERATE a self‑contained test routine that iterates over the recorded solutions and asserts the validation condition
EMIT the source code implementing the dancing‑links construction, Algorithm X enumeration, solution recording, validation, and test routine
