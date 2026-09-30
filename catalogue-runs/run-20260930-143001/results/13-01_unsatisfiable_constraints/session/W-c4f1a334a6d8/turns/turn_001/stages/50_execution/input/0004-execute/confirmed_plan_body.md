DEFINE the variable domain as {1,2,3} for x, y, z
GENERATE all possible assignments of (x, y, z) from the domain
FILTER assignments that satisfy C1: x != y
FILTER remaining assignments that satisfy C2: y != z
FILTER remaining assignments that satisfy C3: z != x
FILTER remaining assignments that satisfy C4: x + y + z = 4
FILTER remaining assignments that satisfy C5: x >= y
FILTER remaining assignments that satisfy C6: y >= z
IF any assignments remain THEN LIST all remaining assignments as valid solutions
ELSE IDENTIFY and EXPLAIN which constraints are mutually contradictory causing unsatisfiability
