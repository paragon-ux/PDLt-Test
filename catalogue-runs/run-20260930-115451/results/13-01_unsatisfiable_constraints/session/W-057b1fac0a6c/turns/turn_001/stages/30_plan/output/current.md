GENERATE all possible triples (x, y, z) where each variable takes values from {1,2,3}
FILTER triples that satisfy C1: x != y, C2: y != z, C3: z != x
FILTER remaining triples that satisfy C4: x + y + z = 4
FILTER remaining triples that satisfy C5: x >= y
FILTER remaining triples that satisfy C6: y >= z
IF any triples remain THEN LIST all remaining triples as solutions
ELSE IDENTIFY which constraints are mutually contradictory and PROVIDE a minimal explanation of the conflict
