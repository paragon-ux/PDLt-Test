PARSE the variable domains for x, y, z
GENERATE all possible assignments of values from {1,2,3} to x, y, z
FILTER assignments that satisfy the inequality constraints x != y, y != z, z != x
FILTER the remaining assignments that satisfy the arithmetic constraint x + y + z = 4
FILTER the remaining assignments that satisfy the ordering constraints x >= y and y >= z
IF any assignments remain THEN EMIT all remaining assignments as solutions
ELSE EMIT a minimal explanation identifying the conflicting constraints that render the problem unsatisfiable
