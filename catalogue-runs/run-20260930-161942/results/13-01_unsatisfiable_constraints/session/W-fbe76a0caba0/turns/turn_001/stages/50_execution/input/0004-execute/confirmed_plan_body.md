PARSE the set of values {1,2,3} and the variables x, y, z
GENERATE all possible assignments of the three values to x, y, z
FILTER assignments that satisfy x != y, y != z, z != x, x + y + z = 4, x >= y, and y >= z
IF any assignments remain THEN ENUMERATE each satisfying assignment
ELSE PROVIDE a brief explanation of why the constraints conflict
