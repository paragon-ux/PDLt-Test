GENERATE all triples (x, y, z) with each variable taking values 1, 2, or 3
FILTER triples to keep only those where x != y, y != z, and z != x
FILTER triples to keep only those where x + y + z = 4
FILTER triples to keep only those where x >= y
FILTER triples to keep only those where y >= z
IF any triples remain THEN ENUMERATE all remaining triples as solutions
ELSE PROVIDE a minimal explanation of the conflicting constraints
