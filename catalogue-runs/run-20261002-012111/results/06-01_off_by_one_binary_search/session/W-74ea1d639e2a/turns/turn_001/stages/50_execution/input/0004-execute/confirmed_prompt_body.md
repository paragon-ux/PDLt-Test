IDENTIFY bug IN binary_search.
EXPLAIN why the bug occurs.
PROVIDE corrected version OF binary_search.
CREATE test suite FOR binary_search WITH arr = [1, 3, 5, 7, 9, 11, 13] AND targets = [1, 7, 13, 4, 0, 14] THAT:
    RUN original binary_search ON arr AND each target TO SHOW incorrect results.
    RUN corrected binary_search ON arr AND each target TO CONFIRM correct results.
