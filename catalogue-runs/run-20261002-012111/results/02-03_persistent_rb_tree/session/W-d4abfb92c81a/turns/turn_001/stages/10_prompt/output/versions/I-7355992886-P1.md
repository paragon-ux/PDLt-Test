IMPLEMENT a persistent functional red‑black tree in Python using path copying.
PROVIDE three operations:
  insert(tree, key) -> new_tree returns a new tree with the key inserted while leaving the original tree unchanged.
  lookup(tree, key) -> bool checks whether a key is present.
  to_sorted_list(tree) -> list returns an in‑order traversal of the tree.
INCLUDE tests that verify persistence, red‑black invariants, and binary‑search‑tree ordering:
  VERIFY that modifying the new tree does not affect the original tree.
  ENSURE red‑black invariants:
    - the root is black.
    - no red parent has a red child.
    - all paths have equal black‑height.
  CONFIRM that the tree maintains binary‑search‑tree ordering.
RETURN the complete Python source code and the test suite.
