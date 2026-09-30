READ the variables x, y, z each taking values from {1, 2, 3}
READ the constraints C1 through C6 as given
GENERATE all possible assignments of x, y, z from the domain {1,2,3}
FOR each assignment DO
EVALUATE each constraint C1–C6 on the assignment
IF the assignment satisfies every constraint THEN
ADD the assignment to the list of solutions
ENDIF
ENDFOR
IF the list of solutions is non‑empty THEN
RETURN the complete list of solutions
ELSE
ANALYZE which constraints cannot be simultaneously satisfied
IDENTIFY a minimal set of conflicting constraints
RETURN a minimal explanation of the conflict
ENDIF
