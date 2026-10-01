TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a persistent red-black tree in Python using path copying. Provide functional operations: insert(tree, key) -> new_tree (returns a new tree with the key inserted while the original remains unchanged), lookup(tree, key) -> bool (checks membership), and to_sorted_list(tree) -> list (produces an in-order traversal). Enforce immutability: after insert(t1, k) -> t2, t1 must remain unchanged. Include tests verifying persistence (modifying t2 does not affect t1), red-black invariants (root is black, no red-red parent-child relationships, equal black-height on all paths), and binary search tree ordering.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- path copying
- insert(tree, key) -> new_tree
- lookup(tree, key) -> bool
- to_sorted_list(tree) -> list
- insert(t1, k) -> t2
- root is black
- no red-red parent-child
- equal black-height on all paths

OPERATOR CORRECTION (host-side mechanical check): the following task entities are missing from the prompt body and MUST appear verbatim, character-for-character: insert(t1, k) -> t2
