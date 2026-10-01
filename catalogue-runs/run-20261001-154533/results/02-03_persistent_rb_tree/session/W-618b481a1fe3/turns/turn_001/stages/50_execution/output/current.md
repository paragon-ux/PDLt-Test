# Persistent Red-Black Tree implementation using path copying
# ------------------------------------------------------------
# Node colors
RED = True
BLACK = False

class Node:
    __slots__ = ("key", "color", "left", "right")
    def __init__(self, key, color=RED, left=None, right=None):
        self.key = key
        self.color = color
        self.left = left
        self.right = right

    def copy(self, *, key=None, color=None, left=None, right=None):
        return Node(
            key if key is not None else self.key,
            color if color is not None else self.color,
            left if left is not None else self.left,
            right if right is not None else self.right,
        )

class PersistentRBTree:
    __slots__ = ("root",)
    def __init__(self, root=None):
        self.root = root

    # Helper: is red?
    @staticmethod
    def _is_red(node):
        return node is not None and node.color == RED

    # Rotate left (path copying)
    def _rotate_left(self, h):
        x = h.right
        h_new = h.copy(right=x.left)
        x_new = x.copy(left=h_new, color=h.color)
        return x_new

    # Rotate right (path copying)
    def _rotate_right(self, h):
        x = h.left
        h_new = h.copy(left=x.right)
        x_new = x.copy(right=h_new, color=h.color)
        return x_new

    # Flip colors (path copying)
    def _flip_colors(self, h):
        h_new = h.copy(color=RED)
        left_new = h.left.copy(color=BLACK) if h.left else None
        right_new = h.right.copy(color=BLACK) if h.right else None
        h_new.left = left_new
        h_new.right = right_new
        return h_new

    def insert(self, key):
        def _insert(node):
            if node is None:
                return Node(key, color=RED)
            if key < node.key:
                left_new = _insert(node.left)
                node = node.copy(left=left_new)
            elif key > node.key:
                right_new = _insert(node.right)
                node = node.copy(right=right_new)
            else:
                # key already present – no change
                return node

            # Fix right-leaning reds
            if self._is_red(node.right) and not self._is_red(node.left):
                node = self._rotate_left(node)
            # Fix two reds in a row
            if self._is_red(node.left) and self._is_red(node.left.left):
                node = self._rotate_right(node)
            # Split 4-nodes
            if self._is_red(node.left) and self._is_red(node.right):
                node = self._flip_colors(node)
            return node

        new_root = _insert(self.root)
        if new_root:
            new_root = new_root.copy(color=BLACK)  # ensure root is black
        return PersistentRBTree(new_root)

    def lookup(self, key):
        node = self.root
        while node:
            if key < node.key:
                node = node.left
            elif key > node.key:
                node = node.right
            else:
                return True
        return False

    def to_sorted_list(self):
        result = []
        def _inorder(node):
            if not node:
                return
            _inorder(node.left)
            result.append(node.key)
            _inorder(node.right)
        _inorder(self.root)
        return result

# ------------------------------------------------------------
# Tests for persistence, red-black invariants, and BST ordering
import unittest

class TestPersistentRBTree(unittest.TestCase):
    def setUp(self):
        self.empty = PersistentRBTree()
        self.t1 = self.empty.insert(10).insert(20).insert(5)

    def test_persistence(self):
        t2 = self.t1.insert(15)
        # t1 should not contain 15
        self.assertFalse(self.t1.lookup(15))
        self.assertTrue(t2.lookup(15))
        # ensure original ordering unchanged
        self.assertEqual(self.t1.to_sorted_list(), [5,10,20])
        self.assertEqual(t2.to_sorted_list(), [5,10,15,20])

    def test_red_black_properties(self):
        def check_properties(node):
            if node is None:
                return 1  # black-height of null leaf
            # No red-red parent-child
            if node.color == RED:
                self.assertTrue(node.left is None or node.left.color == BLACK)
                self.assertTrue(node.right is None or node.right.color == BLACK)
            # BST ordering
            if node.left:
                self.assertLess(node.left.key, node.key)
            if node.right:
                self.assertGreater(node.right.key, node.key)
            left_black = check_properties(node.left)
            right_black = check_properties(node.right)
            self.assertEqual(left_black, right_black)
            return left_black + (1 if node.color == BLACK else 0)
        # root must be black
        self.assertTrue(self.t1.root is None or self.t1.root.color == BLACK)
        check_properties(self.t1.root)

    def test_bst_ordering(self):
        keys = [30, 15, 40, 10, 20, 35, 50]
        tree = PersistentRBTree()
        for k in keys:
            tree = tree.insert(k)
        self.assertEqual(tree.to_sorted_list(), sorted(keys))
        for k in keys:
            self.assertTrue(tree.lookup(k))
        self.assertFalse(tree.lookup(99))

if __name__ == "__main__":
    unittest.main()
