IMPLEMENT a union-find data structure in Python with rollback support.
USE union-by-rank.
DO NOT use path compression.
PROVIDE the following operations:
- make_set(x)
- find(x)
- union(x, y)
- save()
- restore()
DESCRIBE save() as capturing the current state.
DESCRIBE restore() as reverting to the last saved state, undoing all unions performed since the save.
INCLUDE tests that verify:
- basic union-find correctness,
- rollback restoring previous component structure,
- nested save/restore sequences.
LIST the following task entities verbatim: union-find, disjoint set, Python, union-by-rank, no path compression, make_set(x), find(x), union(x, y), save(), restore().
