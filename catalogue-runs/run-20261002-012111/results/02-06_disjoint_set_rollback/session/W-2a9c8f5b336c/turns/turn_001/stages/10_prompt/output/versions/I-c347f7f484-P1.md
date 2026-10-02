IMPLEMENT a union-find (disjoint set) data structure in Python with rollback support.
USE union-by-rank to merge sets.
PROHIBIT path compression.
PROVIDE the following operations:
- make_set to create a new singleton set for element x.
- find to return the representative of the set containing element x without applying path compression.
- union to merge the sets containing elements x and y using union-by-rank.
- save to capture the current state of the data structure.
- restore to revert to the most recent saved state, undoing all unions performed since the last save.
INCLUDE tests that verify basic union-find correctness.
INCLUDE tests that verify that rollback restores the previous component structure.
INCLUDE tests that verify that nested save/restore sequences function correctly.
