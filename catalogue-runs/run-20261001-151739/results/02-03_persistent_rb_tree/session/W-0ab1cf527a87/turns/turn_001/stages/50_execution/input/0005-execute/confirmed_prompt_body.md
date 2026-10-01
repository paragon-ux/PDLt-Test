IMPLEMENT a persistent red-black tree in Python using path copying.
PROVIDE functional operation insert(tree, key) -> new_tree that returns a new tree with the key inserted while the original remains unchanged.
PROVIDE functional operation lookup(tree, key) -> bool that checks membership.
PROVIDE functional operation to_sorted_list(tree) -> list that produces an in-order traversal.
ENFORCE immutability: after insert(t1, k) -> t2, t1 must remain unchanged.
INCLUDE tests verifying persistence (modifying t2 does not affect t1).
INCLUDE tests verifying red-black invariants: root is black; no red-red parent-child; equal black-height on all paths.
INCLUDE tests verifying binary search tree ordering.
