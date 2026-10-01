READ the specifications for a persistent functional red-black tree in Python using path copying
DEFINE a node class with fields: key, color, left, right
IMPLEMENT insert(tree, key) to create a new tree instance with the key inserted while preserving the original tree
IMPLEMENT lookup(tree, key) to return a boolean indicating membership of the key
IMPLEMENT to_sorted_list(tree) to perform an in‑order traversal and return a list of keys
ENFORCE red‑black invariants after each insertion: root is black, no red node has a red child, and all root‑to‑leaf paths contain the same number of black nodes
WRITE unit tests that verify persistence (modifying the tree returned by insert does not affect the original tree), correctness of lookup, correctness of the sorted list output, and adherence to all red‑black invariants
