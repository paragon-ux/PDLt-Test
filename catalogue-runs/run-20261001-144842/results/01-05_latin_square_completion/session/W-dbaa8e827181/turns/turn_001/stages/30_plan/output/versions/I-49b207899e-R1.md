PARSE the provided 7x7 grid and identify cells containing 0 as unknown.
INITIALIZE a constraint‑propagation solver with variables representing each cell and domain {1,…,7}.
SET constraints that each row must contain all numbers 1…7 exactly once.
SET constraints that each column must contain all numbers 1…7 exactly once.
ASSIGN the known non‑zero values to the corresponding variables in the solver.
PROPAGATE constraints to reduce the domains of unknown cells.
IF any cell domain becomes empty THEN abort the search.
IF the puzzle is not fully assigned THEN BACKTRACK using depth‑first search, selecting a variable with the smallest domain, assigning a candidate value, and recursively invoking propagation.
WHEN a complete assignment satisfying all row and column constraints is obtained THEN EMIT the completed 7x7 square.
VERIFY that each row of the emitted square is a permutation of {1,…,7}.
VERIFY that each column of the emitted square is a permutation of {1,…,7}.
