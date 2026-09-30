READ the supplied constraints and domain set
GENERATE all possible assignments of x, y, z from the set {1, 2, 3}
FILTER assignments that satisfy x != y, y != z, z != x, x + y + z = 4, x >= y, and y >= z
IF any assignments remain THEN OUTPUT the list of satisfying assignments, referencing x, y, z, 1, 2, 3, and 4
ELSE OUTPUT a minimal explanation identifying which constraints conflict
