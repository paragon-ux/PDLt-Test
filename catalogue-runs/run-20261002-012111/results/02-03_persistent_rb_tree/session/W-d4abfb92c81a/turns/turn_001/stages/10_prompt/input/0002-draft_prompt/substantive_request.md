TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a persistent functional red-black tree in Python using path copying. Provide three operations: insert(tree, key) -> new_tree returns a new tree with the key inserted while leaving the original tree unchanged, lookup(tree, key) -> bool checks whether a key is present, and to_sorted_list(tree) -> list returns an in‑order traversal of the tree. Include tests that verify persistence (modifying the new tree does not affect the original), enforce red‑black invariants (root is black, no red parent has a red child, all paths have equal black‑height), and validate binary‑search‑tree ordering.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- insert
- lookup
- to_sorted_list
