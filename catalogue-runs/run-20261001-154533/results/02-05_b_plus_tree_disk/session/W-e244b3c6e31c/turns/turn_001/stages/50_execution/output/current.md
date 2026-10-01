```python
import pickle
from collections import deque

class BPlusTreeNode:
    def __init__(self, order, leaf=False):
        self.order = order
        self.leaf = leaf
        self.keys = []
        self.children = []
        # leaf-specific links
        self.prev = None
        self.next = None

class BPlusTree:
    def __init__(self, order=4):
        self.order = order
        self.root = BPlusTreeNode(order, leaf=True)
        self.first_leaf = self.root

    # ---------- Search ----------
    def search(self, key):
        node = self._find_leaf(key)
        for i, k in enumerate(node.keys):
            if k == key:
                return node.children[i]
        return None

    # ---------- Insert ----------
    def insert(self, key, value):
        leaf = self._find_leaf(key)
        self._insert_into_leaf(leaf, key, value)
        if len(leaf.keys) > self.order - 1:
            self._split_leaf(leaf)

    def _find_leaf(self, key):
        node = self.root
        while not node.leaf:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            node = node.children[i]
        return node

    def _insert_into_leaf(self, leaf, key, value):
        i = 0
        while i < len(leaf.keys) and key > leaf.keys[i]:
            i += 1
        leaf.keys.insert(i, key)
        leaf.children.insert(i, value)

    def _split_leaf(self, leaf):
        mid = len(leaf.keys) // 2
        new_leaf = BPlusTreeNode(self.order, leaf=True)
        new_leaf.keys = leaf.keys[mid:]
        new_leaf.children = leaf.children[mid:]
        leaf.keys = leaf.keys[:mid]
        leaf.children = leaf.children[:mid]
        # link leaves
        new_leaf.next = leaf.next
        if leaf.next:
            leaf.next.prev = new_leaf
        leaf.next = new_leaf
        new_leaf.prev = leaf
        # adjust first_leaf if needed
        if self.first_leaf == leaf and new_leaf.keys[0] < leaf.keys[0]:
            self.first_leaf = new_leaf
        # propagate split
        self._insert_into_parent(leaf, new_leaf.keys[0], new_leaf)

    def _insert_into_parent(self, left, key, right):
        if left == self.root:
            new_root = BPlusTreeNode(self.order, leaf=False)
            new_root.keys = [key]
            new_root.children = [left, right]
            self.root = new_root
            return
        parent = self._find_parent(self.root, left)
        i = 0
        while i < len(parent.keys) and key > parent.keys[i]:
            i += 1
        parent.keys.insert(i, key)
        parent.children.insert(i + 1, right)
        if len(parent.keys) > self.order - 1:
            self._split_internal(parent)

    def _split_internal(self, node):
        mid = len(node.keys) // 2
        up_key = node.keys[mid]
        new_node = BPlusTreeNode(self.order, leaf=False)
        new_node.keys = node.keys[mid + 1:]
        new_node.children = node.children[mid + 1:]
        node.keys = node.keys[:mid]
        node.children = node.children[:mid + 1]
        self._insert_into_parent(node, up_key, new_node)

    def _find_parent(self, current, child):
        if current.leaf or current.children[0].leaf:
            return None
        for i, c in enumerate(current.children):
            if c is child:
                return current
            if not c.leaf:
                res = self._find_parent(c, child)
                if res:
                    return res
        return None

    # ---------- Range Scan ----------
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

    # ---------- Serialization ----------
    def serialize(self):
        # BFS traversal storing node type and keys
        data = []
        q = deque([self.root])
        while q:
            node = q.popleft()
            node_dict = {
                'leaf': node.leaf,
                'keys': node.keys,
                'children': None,
                'prev_key': node.prev.keys[0] if node.prev else None,
                'next_key': node.next.keys[0] if node.next else None,
            }
            if node.leaf:
                node_dict['children'] = node.children
            else:
                node_dict['children'] = []
                for child in node.children:
                    q.append(child)
            data.append(node_dict)
        return pickle.dumps(data)

    @classmethod
    def deserialize(cls, blob):
        data = pickle.loads(blob)
        # reconstruct nodes in order
        nodes = []
        for nd in data:
            node = BPlusTreeNode(order=len(nd['keys']) + 1, leaf=nd['leaf'])
            node.keys = nd['keys']
            node.children = nd['children'] if nd['leaf'] else []
            nodes.append(node)
        # link leaves
        leaf_nodes = [n for n in nodes if n.leaf]
        for i, leaf in enumerate(leaf_nodes):
            if i > 0:
                leaf.prev = leaf_nodes[i - 1]
                leaf_nodes[i - 1].next = leaf
        # rebuild internal structure using children indices (assume bfs order)
        idx = 0
        q = deque([nodes[0]])
        while q:
            node = q.popleft()
            if not node.leaf:
                child_count = len(node.keys) + 1
                node.children = nodes[idx + 1: idx + 1 + child_count]
                idx += child_count
                for child in node.children:
                    q.append(child)
        tree = cls()
        tree.root = nodes[0]
        tree.first_leaf = leaf_nodes[0] if leaf_nodes else None
        return tree

# ---------- Test Suite ----------
import unittest

class TestBPlusTree(unittest.TestCase):
    def setUp(self):
        self.tree = BPlusTree(order=4)
        # insert keys to cause splits
        for i in range(1, 11):
            self.tree.insert(i, f"val{i}")

    def test_search(self):
        for i in range(1, 11):
            self.assertEqual(self.tree.search(i), f"val{i}")
        self.assertIsNone(self.tree.search(100))

    def test_range_scan(self):
        expected = [(3, 'val3'), (4, 'val4'), (5, 'val5')]
        self.assertEqual(self.tree.range_scan(3, 5), expected)

    def test_split_structure(self):
        # after inserting 10 keys, root should be internal
        self.assertFalse(self.tree.root.leaf)
        # root should have at least one key
        self.assertGreaterEqual(len(self.tree.root.keys), 1)

    def test_serialize_deserialize(self):
        data = self.tree.serialize()
        new_tree = BPlusTree.deserialize(data)
        for i in range(1, 11):
            self.assertEqual(new_tree.search(i), f"val{i}")
        self.assertEqual(new_tree.range_scan(3, 5), [(3, 'val3'), (4, 'val4'), (5, 'val5')])

if __name__ == '__main__':
    unittest.main()
```
