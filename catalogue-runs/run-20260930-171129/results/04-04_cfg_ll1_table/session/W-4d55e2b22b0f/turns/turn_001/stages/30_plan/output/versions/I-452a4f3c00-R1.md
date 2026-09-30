COMPUTE the FIRST sets for non-terminals E, E', T, T', F
COMPUTE the FOLLOW sets for non-terminals E, E', T, T', F
CONSTRUCT the LL(1) parse table using the computed FIRST and FOLLOW sets
INITIALIZE the parser stack with the start symbol and end marker
SET the input buffer to the token sequence id + id * id followed by end marker
WHILE the top of the stack is not the end marker
IF the top of the stack is a terminal
IF it matches the current input symbol
POP the stack and ADVANCE the input
ELSE
REPORT a parsing error and TERMINATE
ELSE IF the top of the stack is a non-terminal
LOOKUP the parse table entry for (non-terminal, current input symbol)
IF an entry exists
POP the stack
PUSH the right‑hand side symbols of the selected production onto the stack in reverse order
ELSE
REPORT a parsing error and TERMINATE
DISPLAY the current stack contents and the remaining input symbols
ENDWHILE
IF both stack and input are at end marker
REPORT that the input string is ACCEPTED
ELSE
REPORT that the input string is REJECTED
