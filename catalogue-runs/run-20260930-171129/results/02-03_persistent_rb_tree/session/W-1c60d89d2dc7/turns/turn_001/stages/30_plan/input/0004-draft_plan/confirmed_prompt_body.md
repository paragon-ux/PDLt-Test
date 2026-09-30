IMPLEMENT a persistent red-black tree in Python USING path copying.
DEFINE function insert(tree, key) THAT RETURNS a new_tree WITH the key inserted WHILE LEAVING the original tree unchanged.
DEFINE function lookup(tree, key) THAT RETURNS a boolean INDICATING membership of key in the tree.
DEFINE function to_sorted_list(tree) THAT RETURNS a list RESULTING FROM an in-order traversal of the tree.
WRITE tests THAT VERIFY persistence: MODIFICATIONS to the new_tree DO NOT affect the original tree.
WRITE tests THAT VERIFY red-black invariants: THE ROOT IS black, NO red-red parent-child relationships EXIST, AND ALL ROOT-TO-LEAF paths HAVE equal black-height.
WRITE tests THAT VERIFY binary search tree ordering: LEFT CHILD KEYS ARE less THAN node KEY AND RIGHT CHILD KEYS ARE greater.
INCLUDE the OPERATIVE TASK ENTITIES verbatim: insert, lookup, to_sorted_list, persistent, red-black tree, path copying.
