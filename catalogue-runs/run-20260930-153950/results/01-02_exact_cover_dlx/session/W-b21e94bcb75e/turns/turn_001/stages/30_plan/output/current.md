READ the collection of sets S1‑S9 defining the exact cover problem for universe U
BUILD a dancing‑links data structure representing the incidence matrix of sets versus elements
EXECUTE Knuth's Algorithm X on the dancing‑links structure to search for all exact covers of U
FOR each found exact‑cover subcollection, STORE the subcollection
VERIFY that each stored subcollection covers every element of U exactly once
EMIT all verified subcollections as the output
RUN a self‑contained test that iterates over the emitted subcollections and asserts that each element of U appears in exactly one selected set
