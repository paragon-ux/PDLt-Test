READ variables x, y, z each taking values from {1, 2, 3}
DEFINE constraints C1: x != y, C2: y != z, C3: z != x, C4: x + y + z = 4, C5: x >= y, C6: y >= z
GENERATE all possible assignments of x, y, z from the domain
FILTER assignments that satisfy every constraint C1 through C6
IF any assignments remain THEN OUTPUT those assignments
ELSE OUTPUT a statement that no solution exists together with a concise explanation of the conflicting constraints
