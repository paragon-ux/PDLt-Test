READ the specifications for a persistent functional red-black tree in Python using path copying
DEFINE a red-black tree node structure with fields: key, color, left, right
ENSURE that insert(tree, key) returns a new tree instance with the key inserted while the original tree remains unchanged
ENSURE that lookup(tree, key) returns a boolean indicating membership of the key in the tree
ENSURE that to_sorted_list(tree) returns a list of keys obtained via an in-order traversal of the tree
ENFORCE red-black invariants: root node is black, no red node has a red child, and every path from the root to a leaf has the same number of black nodes
WRITE unit tests that verify persistence (modifying the tree returned by insert does not affect the original tree), correctness of lookup, correctness of the sorted list output, and adherence to all red-black invariants
