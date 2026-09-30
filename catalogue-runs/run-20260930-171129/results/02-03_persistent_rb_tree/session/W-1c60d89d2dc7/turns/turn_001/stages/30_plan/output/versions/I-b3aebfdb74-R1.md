DESIGN immutable node representation with fields: key, color, left, right
DESIGN tree wrapper holding reference to root node
IMPLEMENT insert(tree, key) AS:
PERFORM path-copy traversal from root to insertion point creating new nodes along the path
INSERT new red node as leaf
REBALANCE via recoloring and rotations while preserving persistence, returning new root
IMPLEMENT lookup(tree, key) AS:
TRAVERSE from root comparing key, RETURN true if found else false
IMPLEMENT to_sorted_list(tree) AS:
PERFORM in-order traversal of the immutable structure, COLLECT keys into list, RETURN list
WRITE tests for persistence:
CREATE initial tree, CALL insert to obtain new_tree, ASSERT original tree unchanged and new_tree contains key
WRITE tests for red-black invariants on each resulting tree:
ASSERT root is black
ASSERT no red node has red child
ASSERT all paths from root to leaves have equal black-height
WRITE tests for binary search tree ordering on each resulting tree:
ASSERT in-order traversal yields sorted sequence
ASSERT for each node left child keys < node key < right child keys
PACKAGE implementation and tests as deliverable
