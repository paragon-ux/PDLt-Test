TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a union-find (disjoint set) data structure in Python with rollback support. The implementation must use union-by-rank and must not use path compression because path compression prevents rollback. Provide the operations make_set(x), find(x), union(x, y), save(), and restore(). The save() operation captures the current state of the data structure; restore() reverts to the most recent saved state, undoing all unions performed since the save. Include tests verifying basic union-find correctness, that rollback restores the previous component structure, and that nested save/restore sequences function correctly.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- make_set
- find
- union
- save
- restore
