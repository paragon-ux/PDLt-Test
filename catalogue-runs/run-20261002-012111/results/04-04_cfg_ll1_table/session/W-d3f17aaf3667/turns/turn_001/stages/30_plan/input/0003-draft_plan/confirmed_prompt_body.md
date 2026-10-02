COMPUTE FIRST sets for all non-terminals E, E', T, T', F.
COMPUTE FOLLOW sets for all non-terminals E, E', T, T', F.
CONSTRUCT LL(1) parse table using the computed FIRST and FOLLOW sets.
DISPLAY the FIRST sets, FOLLOW sets, and the parse table as a formatted matrix.
PARSE the input string "id + id * id" using the parse table, showing each step with the parsing stack and the remaining input.
USE the following operatives: E, E', T, T', F, id, +, *, (, ).
