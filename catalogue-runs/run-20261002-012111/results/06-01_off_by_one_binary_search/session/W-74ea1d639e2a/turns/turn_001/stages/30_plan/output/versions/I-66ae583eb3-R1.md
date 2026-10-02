IDENTIFY bug IN binary_search implementation
EXPLAIN cause OF identified bug
PROVIDE corrected version OF binary_search
CREATE test suite FOR binary_search WITH arr = [1, 3, 5, 7, 9, 11, 13] AND targets = [1, 7, 13, 4, 0, 14]
    FOR each target IN targets
        RUN original binary_search ON arr AND target
        RECORD result
        IF result is incorrect
            SHOW incorrect result
        ENDIF
        RUN corrected binary_search ON arr AND target
        RECORD result
        CONFIRM result is correct
    ENDFOR
REPORT bug description, corrected code, and test suite outcomes
