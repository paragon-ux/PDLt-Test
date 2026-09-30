READ variables x, y, z with domain {1,2,3}
GENERATE all possible assignments of (x, y, z) from the domain
FILTER assignments where x != y, y != z, and z != x
FILTER assignments where x + y + z = 4
FILTER assignments where x >= y and y >= z
IF any assignments remain THEN
EMIT the list of satisfying assignments
ELSE
EMIT a minimal explanation of the conflicting constraints
