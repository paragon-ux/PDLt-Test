DEFINE variables x, y, z with domain {1, 2, 3}
APPLY constraint C1: x != y
APPLY constraint C2: y != z
APPLY constraint C3: z != x
APPLY constraint C4: x + y + z = 4
APPLY constraint C5: x >= y
APPLY constraint C6: y >= z
DETERMINE if any solution exists for the constraints
IF solution exists THEN
    LIST all solutions
ELSE
    PROVIDE minimal explanation of which constraints conflict
ENDIF
