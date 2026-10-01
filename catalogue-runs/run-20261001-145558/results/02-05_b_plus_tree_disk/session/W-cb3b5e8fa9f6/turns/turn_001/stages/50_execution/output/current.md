import pickle
from collections import deque

class BPlusTreeNode:
    def __init__(self, order, leaf=False):
        self.leaf = leaf
        self.keys = []
        self.children = []  # For leaf: values; for internal: child nodes
        self.next = None  # only for leaf nodes
        self.prev = None  # only for leaf nodes
        self.order = order
        self.parent = None

    def is_full(self):
        return len(self.keys) >= self.order

class BPlusTree:
    def __init__(self, order=4):
        self.order = order
        self.root = BPlusTreeNode(order, leaf=True)
        self.first_leaf = self.root

    def _find_leaf(self, key):
        node = self.root
        while not node.leaf:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            node = node.children[i]
        return node

    def insert(self, key, value):
        leaf = self._find_leaf(key)
        # insert in sorted order
        i = 0
        while i < len(leaf.keys) and key > leaf.keys[i]:
            i += 1
        leaf.keys.insert(i, key)
        leaf.children.insert(i, value)
        if leaf.is_full():
            self._split_leaf(leaf)

    def _split_leaf(self, leaf):
        mid = len(leaf.keys) // 2
        new_leaf = BPlusTreeNode(self.order, leaf=True)
        new_leaf.keys = leaf.keys[mid:]
        new_leaf.children = leaf.children[mid:]
        leaf.keys = leaf.keys[:mid]
        leaf.children = leaf.children[:mid]
        # adjust linked list
        new_leaf.next = leaf.next
        if new_leaf.next:
            new_leaf.next.prev = new_leaf
        leaf.next = new_leaf
        new_leaf.prev = leaf
        # promote first key of new leaf
        promote_key = new_leaf.keys[0]
        self._insert_in_parent(leaf, promote_key, new_leaf)

    def _insert_in_parent(self, left, key, right):
        if left.parent is None:
            # create new root
            new_root = BPlusTreeNode(self.order, leaf=False)
            new_root.keys = [key]
            new_root.children = [left, right]
            left.parent = new_root
            right.parent = new_root
            self.root = new_root
            return
        parent = left.parent
        i = 0
        while i < len(parent.keys) and key > parent.keys[i]:
            i += 1
        parent.keys.insert(i, key)
        parent.children.insert(i + 1, right)
        right.parent = parent
        if parent.is_full():
            self._split_internal(parent)

    def _split_internal(self, node):
        mid = len(node.keys) // 2
        promote_key = node.keys[mid]
        new_node = BPlusTreeNode(self.order, leaf=False)
        new_node.keys = node.keys[mid + 1:]
        new_node.children = node.children[mid + 1:]
        for child in new_node.children:
            child.parent = new_node
        node.keys = node.keys[:mid]
        node.children = node.children[:mid + 1]
        self._insert_in_parent(node, promote_key, new_node)

    def search(self, key):
        leaf = self._find_leaf(key)
        for i, k in enumerate(leaf.keys):
            if k == key:
                return leaf.children[i]
        return None

    def range_scan(self, lo, hi):
        results = []
        leaf = self._find_leaf(lo)
        while leaf:
            for k, v in zip(leaf.keys, leaf.children):
                if lo <= k <= hi:
                    results.append((k, v))
                elif k > hi:
                    return results
            leaf = leaf.next
        return results

    def serialize(self):
        # Simple pickle based serialization for demonstration
        return pickle.dumps(self)

    @staticmethod
    def deserialize(data):
        return pickle.loads(data)

# Test suite
import unittest

class TestBPlusTree(unittest.TestCase):
    def setUp(self):
        self.tree = BPlusTree(order=4)
        for i in range(1, 21):
            self.tree.insert(i, f"val{i}")

    def test_search(self):
        for i in range(1, 21):
            self.assertEqual(self.tree.search(i), f"val{i}")
        self.assertIsNone(self.tree.search(100))

    def test_range_scan(self):
        result = self.tree.range_scan(5, 15)
        expected = [(i, f"val{i}") for i in range(5, 16)]
        self.assertEqual(result, expected)

    def test_leaf_split(self):
        # after inserting 20 keys, tree height should be >1
        self.assertFalse(self.tree.root.leaf)
        # root should have at least one key
        self.assertGreater(len(self.tree.root.keys), 0)

    def test_internal_split(self):
        # Insert many keys to force internal splits
        for i in range(21, 101):
            self.tree.insert(i, f"val{i}")
        self.assertFalse(self.tree.root.leaf)
        # check tree integrity via search
        for i in range(1, 101):
            self.assertEqual(self.tree.search(i), f"val{i}")

    def test_serialize_deserialize(self):
        data = self.tree.serialize()
        new_tree = BPlusTree.deserialize(data)
        for i in range(1, 101):
            self.assertEqual(new_tree.search(i), f"val{i}")
        self.assertEqual(new_tree.range_scan(10, 20), [(i, f"val{i}") for i in range(10, 21)])

if __name__ == "__main__":
    unittest.main()
