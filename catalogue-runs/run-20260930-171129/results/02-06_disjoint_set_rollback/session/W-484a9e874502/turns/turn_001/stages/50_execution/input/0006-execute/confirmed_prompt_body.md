IMPLEMENT a union-find (disjoint set) data structure in Python using union-by-rank (no path compression).
PROVIDE the following operations:
- make_set(x) to create a singleton set containing element x.
- find(x) to return the representative of the set containing x.
- union(x, y) to merge the sets containing x and y according to union-by-rank.
- save() to capture the current state of the data structure.
- restore() to revert to the most recently saved state, undoing all unions performed since that save.
INCLUDE tests that verify:
- basic union-find correctness for make_set, find, and union.
- rollback functionality correctly restores the component structure after a restore.
- nested save and restore sequences behave as expected.
