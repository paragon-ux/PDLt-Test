IMPLEMENT a persistent (functional) red-black tree in Python using path copying.
DEFINE function insert(tree, key) -> new_tree that returns a new tree with the key inserted, leaving the original tree unchanged.
DEFINE function lookup(tree, key) -> bool that returns true if the key exists in the tree, otherwise false.
DEFINE function to_sorted_list(tree) -> list that returns the keys of the tree in sorted order.
ENSURE persistence such that after INSERT(t1, k) -> t2, t1 remains unchanged.
INCLUDE tests that VERIFY persistence (modifying t2 does not affect t1), red-black invariants (root is black, no red-red parent-child, equal black height on all paths), and BST ordering.
