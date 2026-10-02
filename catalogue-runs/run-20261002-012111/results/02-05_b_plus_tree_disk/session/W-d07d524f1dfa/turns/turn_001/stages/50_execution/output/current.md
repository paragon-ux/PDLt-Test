class BPlusTreeNode:
    def __init__(self, leaf=False):
        self.leaf = leaf
        self.keys = []
        self.children = []  # for internal nodes: child pointers; for leaves: values
        self.next = None  # doubly linked list for leaves
        self.prev = None

class BPlusTree:
    def __init__(self, order=4):
        if order < 3:
            raise ValueError("Order must be at least 3")
        self.order = order
        self.root = BPlusTreeNode(leaf=True)

    def _find_leaf(self, key):
        node = self.root
        while not node.leaf:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            node = node.children[i]
        return node

    def search(self, key):
        leaf = self._find_leaf(key)
        for i, k in enumerate(leaf.keys):
            if k == key:
                return leaf.children[i]
        return None

    def insert(self, key, value):
        leaf = self._find_leaf(key)
        # insert in sorted order
        i = 0
        while i < len(leaf.keys) and leaf.keys[i] < key:
            i += 1
        leaf.keys.insert(i, key)
        leaf.children.insert(i, value)
        if len(leaf.keys) > self.order - 1:
            self._split_leaf(leaf)

    def _split_leaf(self, leaf):
        mid = len(leaf.keys) // 2
        new_leaf = BPlusTreeNode(leaf=True)
        new_leaf.keys = leaf.keys[mid:]
        new_leaf.children = leaf.children[mid:]
        leaf.keys = leaf.keys[:mid]
        leaf.children = leaf.children[:mid]
        # link list
        new_leaf.next = leaf.next
        if new_leaf.next:
            new_leaf.next.prev = new_leaf
        leaf.next = new_leaf
        new_leaf.prev = leaf
        # promote first key of new leaf
        promote_key = new_leaf.keys[0]
        self._insert_in_parent(leaf, promote_key, new_leaf)

    def _insert_in_parent(self, left, key, right):
        if left == self.root:
            new_root = BPlusTreeNode(leaf=False)
            new_root.keys = [key]
            new_root.children = [left, right]
            self.root = new_root
            return
        parent = self._find_parent(self.root, left)
        i = 0
        while i < len(parent.keys) and key >= parent.keys[i]:
            i += 1
        parent.keys.insert(i, key)
        parent.children.insert(i + 1, right)
        if len(parent.keys) > self.order - 1:
            self._split_internal(parent)

    def _split_internal(self, node):
        mid = len(node.keys) // 2
        promote_key = node.keys[mid]
        new_node = BPlusTreeNode(leaf=False)
        new_node.keys = node.keys[mid + 1:]
        new_node.children = node.children[mid + 1:]
        node.keys = node.keys[:mid]
        node.children = node.children[:mid + 1]
        self._insert_in_parent(node, promote_key, new_node)

    def _find_parent(self, current, child):
        # helper to find parent of a given child node
        if current.leaf or current.children[0].leaf:
            return None
        for c in current.children:
            if c is child:
                return current
        for c in current.children:
            if not c.leaf:
                p = self._find_parent(c, child)
                if p:
                    return p
        return None

    def range_scan(self, lo, hi):
        result = []
        leaf = self._find_leaf(lo)
        while leaf:
            for k, v in zip(leaf.keys, leaf.children):
                if lo <= k <= hi:
                    result.append((k, v))
                elif k > hi:
                    return result
            leaf = leaf.next
        return result

    def serialize(self):
        # simple page-level serialization using pickle of the whole tree
        import pickle
        return pickle.dumps(self)

    @staticmethod
    def deserialize(data):
        import pickle
        return pickle.loads(data)

# Test suite
import unittest

class TestBPlusTree(unittest.TestCase):
    def setUp(self):
        self.tree = BPlusTree(order=4)
        for i in range(1, 11):
            self.tree.insert(i, f"val{i}")

    def test_search(self):
        for i in range(1, 11):
            self.assertEqual(self.tree.search(i), f"val{i}")
        self.assertIsNone(self.tree.search(999))

    def test_range_scan(self):
        result = self.tree.range_scan(3, 7)
        expected = [(i, f"val{i}") for i in range(3, 8)]
        self.assertEqual(result, expected)

    def test_split(self):
        # after insertions above, root should be internal
        self.assertFalse(self.tree.root.leaf)
        # ensure leaf linking works
        first_leaf = self.tree.root.children[0]
        second_leaf = self.tree.root.children[1]
        self.assertIs(first_leaf.next, second_leaf)
        self.assertIs(second_leaf.prev, first_leaf)

    def test_serialize_deserialize(self):
        data = self.tree.serialize()
        new_tree = BPlusTree.deserialize(data)
        for i in range(1, 11):
            self.assertEqual(new_tree.search(i), f"val{i}")
        self.assertEqual(new_tree.range_scan(5, 9), [(i, f"val{i}") for i in range(5, 10)])

if __name__ == "__main__":
    unittest.main()
