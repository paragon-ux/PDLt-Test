DEFINE a node class with fields key, color, left child, right child
DEFINE a tree class that holds a reference to the root node
IMPLEMENT a persistent insert function that performs path copying and returns a new tree
IMPLEMENT a lookup function that returns true if a key exists in the tree
IMPLEMENT a to_sorted_list function that returns the keys in sorted order via in-order traversal
WRITE tests that create an initial tree, insert a key to obtain a new tree, and VERIFY that the original tree remains unchanged
WRITE tests that verify red-black tree invariants: root is black, no red-red parent-child relationships, equal black height on all paths
WRITE tests that verify binary search tree ordering of keys
RUN all tests to confirm persistence, invariants, and correct ordering
