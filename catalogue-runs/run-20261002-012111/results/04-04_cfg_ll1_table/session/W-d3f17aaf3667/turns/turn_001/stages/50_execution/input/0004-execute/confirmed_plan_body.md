COMPUTE FIRST sets for non-terminals E, E', T, T', F.
COMPUTE FOLLOW sets for non-terminals E, E', T, T', F.
CONSTRUCT LL(1) parse table using the computed FIRST and FOLLOW sets.
FORMAT the FIRST sets, FOLLOW sets, and parse table as a readable matrix.
INITIALIZE parsing stack with start symbol E and input pointer at the beginning of the string "id + id * id".
WHILE parsing stack is not empty DO
    READ the top symbol of the stack and the current input token.
    IF the top symbol is a terminal THEN
        IF it matches the current input token THEN
            POP the terminal from the stack.
            ADVANCE the input pointer.
        ELSE
            SIGNAL a parsing error.
        ENDIF
    ELSE IF the top symbol is a non-terminal THEN
        LOOKUP the parse-table entry for (top symbol, current input token).
        IF entry exists THEN
            POP the non-terminal.
            PUSH the production symbols onto the stack in reverse order.
        ELSE
            SIGNAL a parsing error.
        ENDIF
    ENDIF
    RECORD the current stack contents and the remaining input.
ENDWHILE
EMIT the recorded parsing steps as a step-by-step trace showing the stack and remaining input.
