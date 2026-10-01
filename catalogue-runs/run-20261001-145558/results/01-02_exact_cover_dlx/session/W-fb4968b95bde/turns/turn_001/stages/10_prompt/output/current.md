READ the definition of Universe U = {1,2,3,4,5,6,7,8,9}
READ the nine sets S1‑S9 as provided
IMPLEMENT Knuth's Algorithm X using dancing links to enumerate all exact covers of U by subsets of S1‑S9
FOR each exact cover found
    VERIFY that every element of U appears exactly once in the cover
END_FOR
OUTPUT all exact covers that satisfy the verification
INCLUDE a self‑contained test that asserts each solution covers every element of U exactly once
