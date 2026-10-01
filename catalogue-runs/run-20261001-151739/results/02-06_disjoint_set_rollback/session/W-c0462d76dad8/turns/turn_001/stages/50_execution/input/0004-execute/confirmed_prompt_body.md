READ the request for a union-find data structure with rollback support in Python.
DEFINE operation make_set(x) TO create a new singleton set containing element x.
DEFINE operation find(x) TO return the representative of the set containing x, using union-by-rank without path compression.
DEFINE operation union(x, y) TO merge the sets containing x and y using union-by-rank.
DEFINE operation save() TO capture the current state of the union-find structure for later restoration.
DEFINE operation restore() TO revert the union-find structure to the most recent saved state, undoing all unions performed since that save.
PROVIDE tests THAT verify basic union-find correctness.
PROVIDE tests THAT verify rollback restores the previous component structure after a restore.
PROVIDE tests THAT verify nested save/restore sequences correctly handle multiple layers of saved states.
