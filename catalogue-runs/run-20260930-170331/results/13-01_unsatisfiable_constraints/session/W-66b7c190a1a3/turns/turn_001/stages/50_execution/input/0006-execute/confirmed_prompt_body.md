READ variables x, y, z with domain {1, 2, 3}
READ constraints C1: x != y, C2: y != z, C3: z != x, C4: x + y + z = 4, C5: x >= y, C6: y >= z
EVALUATE all possible assignments of x, y, z that satisfy constraints C1 through C6
IF any assignments satisfy all constraints THEN
LIST all satisfying assignments
ELSE
PROVIDE a minimal explanation identifying the conflicting constraints that make the problem unsatisfiable
ENDIF
