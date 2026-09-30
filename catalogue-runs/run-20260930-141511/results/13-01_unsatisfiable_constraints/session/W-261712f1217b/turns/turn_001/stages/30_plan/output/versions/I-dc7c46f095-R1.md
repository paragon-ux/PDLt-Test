READ the variables x, y, and z and the constraints C1 through C6
GENERATE all possible assignments of integer values 1, 2, or 3 to x, y, and z
FOR each assignment
EVALUATE whether the assignment satisfies every constraint C1, C2, C3, C4, C5, and C6
IF the assignment satisfies all constraints THEN ADD the assignment to a collection of satisfying assignments
ENDFOR
IF the collection of satisfying assignments is non‑empty THEN
PREPARE a list of all satisfying assignments for output
ELSE
IDENTIFY a minimal subset of constraints that are mutually contradictory
PREPARE a brief explanation of the conflicting constraints for output
ENDIF
