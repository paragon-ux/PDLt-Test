READ the request to implement a union-find (disjoint set) data structure in Python with rollback support using union-by-rank (no path compression).
PROVIDE functions: make_set(x), find(x), union(x, y), save() to capture current state, and restore() to revert to the last saved state, undoing all unions performed since the save.
INCLUDE tests verifying basic union-find correctness, rollback restoring previous component structure, and nested save/restore sequences.
ENSURE the implementation uses union-by-rank and does not apply path compression.
ENSURE the rollback mechanism correctly restores the component structure to the state captured by the most recent save call.
ENSURE multiple nested save and restore calls behave correctly, each restore reverting to the appropriate prior saved state.
