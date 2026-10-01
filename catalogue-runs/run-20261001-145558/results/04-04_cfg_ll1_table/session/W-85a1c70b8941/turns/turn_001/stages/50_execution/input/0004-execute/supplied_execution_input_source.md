Given the following context-free grammar:

E  -> T E'
E' -> + T E' | epsilon
T  -> F T'
T' -> * F T' | epsilon
F  -> ( E ) | id

Build the LL(1) parse table by computing FIRST and FOLLOW sets for all non-terminals. Display the FIRST sets, FOLLOW sets, and the resulting parse table as a formatted matrix. Then use the table to parse the input string "id + id * id" and show the step-by-step parse trace (stack contents and remaining input at each step).
