# bplustree.py
import pickle
from collections import deque

class Node:
    def __init__(self, order, is_leaf=False):
        self.order = order
        self.is_leaf = is_leaf
        self.keys = []
        self.parent = None

class LeafNode(Node):
    def __init__(self, order):
        super().__init__(order, is_leaf=True)
        self.values = []
        self.prev = None
        self.next = None

class InternalNode(Node):
    def __init__(self, order):
        super().__init__(order, is_leaf=False)
        self.children = []

class BPlusTree:
    def __init__(self, order=4):
        self.order = order
        self.root = LeafNode(order)
        self.first_leaf = self.root
        self.last_leaf = self.root

    # ---------- search ----------
    def _find_leaf(self, key):
        node = self.root
        while not node.is_leaf:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            node = node.children[i]
        return node

    def search(self, key):
        leaf = self._find_leaf(key)
        for i, k in enumerate(leaf.keys):
            if k == key:
                return leaf.values[i]
        return None

    # ---------- insert ----------
    def insert(self, key, value):
        leaf = self._find_leaf(key)
        # insert in sorted order
        i = 0
        while i < len(leaf.keys) and leaf.keys[i] < key:
            i += 1
        leaf.keys.insert(i, key)
        leaf.values.insert(i, value)
        if len(leaf.keys) > self.order:
            self._split_leaf(leaf)

    def _split_leaf(self, leaf):
        mid = len(leaf.keys) // 2
        new_leaf = LeafNode(self.order)
        new_leaf.keys = leaf.keys[mid:]
        new_leaf.values = leaf.values[mid:]
        leaf.keys = leaf.keys[:mid]
        leaf.values = leaf.values[:mid]
        # adjust linked list
        new_leaf.next = leaf.next
        if leaf.next:
            leaf.next.prev = new_leaf
        leaf.next = new_leaf
        new_leaf.prev = leaf
        if self.last_leaf is leaf:
            self.last_leaf = new_leaf
        # promote key
        promote_key = new_leaf.keys[0]
        self._insert_in_parent(leaf, promote_key, new_leaf)

    def _insert_in_parent(self, left, key, right):
        if left is self.root:
            new_root = InternalNode(self.order)
            new_root.keys = [key]
            new_root.children = [left, right]
            left.parent = new_root
            right.parent = new_root
            self.root = new_root
            return
        parent = left.parent
        i = 0
        while i < len(parent.children) and parent.children[i] is not left:
            i += 1
        parent.keys.insert(i, key)
        parent.children.insert(i + 1, right)
        right.parent = parent
        if len(parent.keys) > self.order:
            self._split_internal(parent)

    def _split_internal(self, node):
        mid = len(node.keys) // 2
        promote_key = node.keys[mid]
        new_node = InternalNode(self.order)
        new_node.keys = node.keys[mid + 1:]
        new_node.children = node.children[mid + 1:]
        for child in new_node.children:
            child.parent = new_node
        node.keys = node.keys[:mid]
        node.children = node.children[:mid + 1]
        self._insert_in_parent(node, promote_key, new_node)

    # ---------- range scan ----------
    def range_scan(self, lo, hi):
        leaf = self._find_leaf(lo)
        results = []
        while leaf:
            for k, v in zip(leaf.keys, leaf.values):
                if lo <= k <= hi:
                    results.append((k, v))
                elif k > hi:
                    return results
            leaf = leaf.next
        return results

    # ---------- serialize / deserialize ----------
    def serialize(self):
        # Use pickle for simplicity; it captures object graph including links.
        return pickle.dumps(self)

    @staticmethod
    def deserialize(data):
        tree = pickle.loads(data)
        # After unpickling, ensure leaf linkage consistency (pickle preserves it).
        return tree

# ---------- test suite ----------
import unittest

class TestBPlusTree(unittest.TestCase):
    def setUp(self):
        self.tree = BPlusTree(order=4)
        # Insert enough keys to cause multiple splits
        for i in range(1, 21):
            self.tree.insert(i, f"val{i}")

    def test_search_existing(self):
        self.assertEqual(self.tree.search(10), "val10")

    def test_search_missing(self):
        self.assertIsNone(self.tree.search(100))

    def test_range_scan(self):
        result = self.tree.range_scan(5, 15)
        expected = [(i, f"val{i}") for i in range(5, 16)]
        self.assertEqual(result, expected)

    def test_leaf_split_and_root_split(self):
        # After inserting 20 keys into order 4, tree depth should be >1
        self.assertFalse(isinstance(self.tree.root, LeafNode))
        # Verify leaf links cover all keys in order
        leaf = self.tree.first_leaf
        all_keys = []
        while leaf:
            all_keys.extend(leaf.keys)
            leaf = leaf.next
        self.assertEqual(all_keys, list(range(1, 21)))

    def test_serialize_deserialize(self):
        data = self.tree.serialize()
        new_tree = BPlusTree.deserialize(data)
        # Structure should be identical
        self.assertEqual(new_tree.range_scan(1, 20), self.tree.range_scan(1, 20))
        self.assertEqual(new_tree.search(7), "val7")
        self.assertEqual(new_tree.search(21), None)
        # Verify leaf linkage after round‑trip
        leaf = new_tree.first_leaf
        keys = []
        while leaf:
            keys.extend(leaf.keys)
            leaf = leaf.next
        self.assertEqual(keys, list(range(1, 21)))

if __name__ == "__main__":
    unittest.main()
