COMPUTE the FIRST sets for each non-terminal: E, E', T, T', F
COMPUTE the FOLLOW sets for each non-terminal: E, E', T, T', F
BUILD the LL(1) parse table for the grammar
PARSE the input string "id + id * id" using the constructed parse table, RECORDING the parser stack contents and remaining input at each step
LIST the operative task entities: E, E', T, T', F, id, +, *, (, ), id + id * id
EMIT the FIRST sets, FOLLOW sets, parse table, parse trace, and entity list as the final output
