"""Persistent functional red‑black tree implementation using path copying.

The tree is immutable: insert returns a new tree sharing unchanged sub‑structures with the original.
The implementation includes:
- Node dataclass with key, color, left, right.
- Tree dataclass with root.
- insert, lookup, to_sorted_list operations.
- Helper rotations and fix‑up for red‑black properties.
- Verification functions for red‑black invariants and BST ordering.
- Test suite exercising persistence, invariants, and ordering.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

# Colors
RED = True
BLACK = False

@dataclass(frozen=True)
class Node:
    key: int
    color: bool = RED
    left: Optional[Node] = None
    right: Optional[Node] = None

    def is_red(self) -> bool:
        return self.color == RED

    def with_children(self, left: Optional[Node], right: Optional[Node]) -> Node:
        return Node(self.key, self.color, left, right)

    def with_color(self, color: bool) -> Node:
        return Node(self.key, color, self.left, self.right)

    def replace(self, *, key=None, color=None, left=None, right=None) -> Node:
        return Node(
            self.key if key is None else key,
            self.color if color is None else color,
            self.left if left is None else left,
            self.right if right is None else right,
        )

@dataclass(frozen=True)
class Tree:
    root: Optional[Node] = None

# ---- Helper functions ----------------------------------------------------

def rotate_left(h: Node) -> Node:
    assert h.right is not None
    x = h.right
    return x.with_children(
        h.with_children(h.left, x.left).with_color(RED),
        x.right,
    ).with_color(h.color)

def rotate_right(h: Node) -> Node:
    assert h.left is not None
    x = h.left
    return x.with_children(
        x.left,
        h.with_children(x.right, h.right).with_color(RED),
    ).with_color(h.color)

def flip_colors(h: Node) -> Node:
    return h.with_color(RED).replace(
        left=h.left.with_color(BLACK) if h.left else None,
        right=h.right.with_color(BLACK) if h.right else None,
    )

def is_red(node: Optional[Node]) -> bool:
    return node.is_red() if node else False

# ---- Core operations ------------------------------------------------------

def insert(tree: Tree, key: int) -> Tree:
    def _insert(node: Optional[Node]) -> Node:
        if node is None:
            # New red node
            return Node(key)
        if key < node.key:
            new_left = _insert(node.left)
            node = node.with_children(new_left, node.right)
        elif key > node.key:
            new_right = _insert(node.right)
            node = node.with_children(node.left, new_right)
        else:
            # key already present – no change
            return node
        # Fix right‑leaning reds
        if is_red(node.right) and not is_red(node.left):
            node = rotate_left(node)
        # Fix two reds in a row
        if is_red(node.left) and is_red(node.left.left):
            node = rotate_right(node)
        # Split 4‑node
        if is_red(node.left) and is_red(node.right):
            node = flip_colors(node)
        return node

    new_root = _insert(tree.root)
    # Ensure root is black
    if new_root.is_red():
        new_root = new_root.with_color(BLACK)
    return Tree(new_root)

def lookup(tree: Tree, key: int) -> bool:
    node = tree.root
    while node:
        if key < node.key:
            node = node.left
        elif key > node.key:
            node = node.right
        else:
            return True
    return False

def to_sorted_list(tree: Tree) -> List[int]:
    def inorder(node: Optional[Node], acc: List[int]):
        if not node:
            return
        inorder(node.left, acc)
        acc.append(node.key)
        inorder(node.right, acc)
    result: List[int] = []
    inorder(tree.root, result)
    return result

# ---- Verification ---------------------------------------------------------

def _black_height(node: Optional[Node]) -> Optional[int]:
    if node is None:
        return 0
    left = _black_height(node.left)
    right = _black_height(node.right)
    if left is None or right is None or left != right:
        return None
    return left + (0 if node.is_red() else 1)

def verify_red_black_invariants(tree: Tree) -> bool:
    # Root must be black
    if tree.root and tree.root.is_red():
        return False
    # No red node has red child
    def no_red_red(node: Optional[Node]) -> bool:
        if not node:
            return True
        if node.is_red():
            if (node.left and node.left.is_red()) or (node.right and node.right.is_red()):
                return False
        return no_red_red(node.left) and no_red_red(node.right)
    if not no_red_red(tree.root):
        return False
    # Equal black height on all paths
    return _black_height(tree.root) is not None

def verify_bst_ordering(tree: Tree) -> bool:
    lst = to_sorted_list(tree)
    return lst == sorted(lst)

# ---- Tests -----------------------------------------------------------------
import unittest

class PersistentRedBlackTreeTest(unittest.TestCase):
    def test_persistence_single_insert(self):
        empty = Tree()
        t1 = insert(empty, 10)
        t2 = insert(t1, 5)
        # original t1 unchanged
        self.assertEqual(to_sorted_list(t1), [10])
        self.assertEqual(to_sorted_list(t2), [5, 10])
        self.assertTrue(verify_red_black_invariants(t2))
        self.assertTrue(verify_bst_ordering(t2))
    def test_multiple_insertions(self):
        keys = [20, 15, 25, 10, 18, 22, 30]
        tree = Tree()
        snapshots = []
        for k in keys:
            new_tree = insert(tree, k)
            # tree unchanged
            self.assertEqual(to_sorted_list(tree), sorted([x.key for x in snapshots]))
            snapshots.append(new_tree.root)  # just to capture state count
            self.assertTrue(verify_red_black_invariants(new_tree))
            self.assertTrue(verify_bst_ordering(new_tree))
            tree = new_tree
    def test_lookup(self):
        tree = Tree()
        for k in [3, 1, 4, 1, 5, 9, 2, 6, 5]:
            tree = insert(tree, k)
        for k in range(10):
            self.assertEqual(lookup(tree, k), k in [1,2,3,4,5,6,9])

if __name__ == "__main__":
    unittest.main()
