# bplustree.py
"""Implementation of a configurable order B+ tree with leaf linking, serialization, and a test suite.

Features:
- Configurable order (max children per internal node), default 4.
- All values stored in leaf nodes; internal nodes store only routing keys.
- Leaves are doubly‑linked for efficient range scans.
- Operations: insert(key, value), search(key), range_scan(lo, hi).
- Page‑level serialization to bytes and deserialization restoring exact structure.
- Test suite verifying leaf/internal splits, search, range scan, and serialize/deserialize round‑trip.
"""

import struct
from collections import deque
from typing import Any, List, Optional, Tuple


class LeafNode:
    __slots__ = ("keys", "values", "prev", "next", "parent")

    def __init__(self):
        self.keys: List[Any] = []
        self.values: List[Any] = []
        self.prev: Optional["LeafNode"] = None
        self.next: Optional["LeafNode"] = None
        self.parent: Optional["InternalNode"] = None

    def is_full(self, order: int) -> bool:
        return len(self.keys) > order - 1  # max entries = order - 1

    def insert(self, key, value):
        # Insert while maintaining sorted order of keys
        i = 0
        while i < len(self.keys) and self.keys[i] < key:
            i += 1
        self.keys.insert(i, key)
        self.values.insert(i, value)

    def split(self, order: int) -> Tuple[Any, "LeafNode"]:
        mid = len(self.keys) // 2
        new_leaf = LeafNode()
        new_leaf.keys = self.keys[mid:]
        new_leaf.values = self.values[mid:]
        self.keys = self.keys[:mid]
        self.values = self.values[:mid]
        # Adjust sibling links
        new_leaf.next = self.next
        if self.next:
            self.next.prev = new_leaf
        self.next = new_leaf
        new_leaf.prev = self
        return new_leaf.keys[0], new_leaf

    def serialize(self) -> bytes:
        # Node type 0 for leaf
        data = struct.pack("!B", 0)
        data += struct.pack("!I", len(self.keys))
        for k, v in zip(self.keys, self.values):
            k_bytes = repr(k).encode('utf-8')
            v_bytes = repr(v).encode('utf-8')
            data += struct.pack("!I", len(k_bytes)) + k_bytes
            data += struct.pack("!I", len(v_bytes)) + v_bytes
        # sibling offsets will be filled later during tree serialization
        return data


class InternalNode:
    __slots__ = ("keys", "children", "parent")

    def __init__(self):
        self.keys: List[Any] = []
        self.children: List[Any] = []  # can be LeafNode or InternalNode
        self.parent: Optional["InternalNode"] = None

    def is_full(self, order: int) -> bool:
        return len(self.children) > order

    def insert_child(self, key, child):
        # Insert key and child keeping keys sorted; child list has len(keys)+1
        i = 0
        while i < len(self.keys) and self.keys[i] < key:
            i += 1
        self.keys.insert(i, key)
        self.children.insert(i + 1, child)
        child.parent = self

    def split(self, order: int) -> Tuple[Any, "InternalNode"]:
        mid = len(self.keys) // 2
        split_key = self.keys[mid]
        new_node = InternalNode()
        new_node.keys = self.keys[mid + 1:]
        new_node.children = self.children[mid + 1:]
        for child in new_node.children:
            child.parent = new_node
        self.keys = self.keys[:mid]
        self.children = self.children[:mid + 1]
        return split_key, new_node

    def serialize(self) -> bytes:
        data = struct.pack("!B", 1)  # Node type 1 for internal
        data += struct.pack("!I", len(self.keys))
        for k in self.keys:
            k_bytes = repr(k).encode('utf-8')
            data += struct.pack("!I", len(k_bytes)) + k_bytes
        # child offsets will be filled later
        return data


class BPlusTree:
    def __init__(self, order: int = 4):
        self.order = order
        self.root: Any = LeafNode()
        # ensure leaf list pointers
        self.first_leaf = self.root
        self.last_leaf = self.root

    # ---- SEARCH -------------------------------------------------
    def search(self, key) -> Optional[Any]:
        leaf = self._find_leaf(key)
        for i, k in enumerate(leaf.keys):
            if k == key:
                return leaf.values[i]
        return None

    # ---- INSERT -------------------------------------------------
    def insert(self, key, value):
        leaf = self._find_leaf(key)
        leaf.insert(key, value)
        if leaf.is_full(self.order):
            self._handle_leaf_split(leaf)

    def _handle_leaf_split(self, leaf: LeafNode):
        split_key, new_leaf = leaf.split(self.order)
        # Update first/last leaf references
        if leaf == self.last_leaf:
            self.last_leaf = new_leaf
        # Insert new leaf into parent chain
        if leaf.parent is None:
            # create new root
            new_root = InternalNode()
            new_root.keys = [split_key]
            new_root.children = [leaf, new_leaf]
            leaf.parent = new_root
            new_leaf.parent = new_root
            self.root = new_root
        else:
            self._insert_in_parent(leaf.parent, split_key, new_leaf)

    def _insert_in_parent(self, parent: InternalNode, key, child):
        parent.insert_child(key, child)
        if parent.is_full(self.order):
            self._handle_internal_split(parent)

    def _handle_internal_split(self, node: InternalNode):
        split_key, new_node = node.split(self.order)
        if node.parent is None:
            new_root = InternalNode()
            new_root.keys = [split_key]
            new_root.children = [node, new_node]
            node.parent = new_root
            new_node.parent = new_root
            self.root = new_root
        else:
            self._insert_in_parent(node.parent, split_key, new_node)

    # ---- RANGE SCAN ---------------------------------------------
    def range_scan(self, lo, hi) -> List[Any]:
        result = []
        leaf = self._find_leaf(lo)
        while leaf:
            for k, v in zip(leaf.keys, leaf.values):
                if lo <= k <= hi:
                    result.append(v)
                elif k > hi:
                    return result
            leaf = leaf.next
        return result

    # ---- HELPERS ------------------------------------------------
    def _find_leaf(self, key) -> LeafNode:
        node = self.root
        while isinstance(node, InternalNode):
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            node = node.children[i]
        return node

    # ---- SERIALIZATION ------------------------------------------
    def serialize(self) -> bytes:
        # Breadth‑first traversal to assign offsets
        nodes = []
        offsets = {}
        queue = deque([self.root])
        while queue:
            node = queue.popleft()
            offsets[id(node)] = len(nodes)
            nodes.append(node)
            if isinstance(node, InternalNode):
                for child in node.children:
                    queue.append(child)
        # Serialize each node with placeholder child offsets
        serialized_nodes = []
        for node in nodes:
            if isinstance(node, LeafNode):
                data = node.serialize()
                # placeholders for prev/next offsets (4 bytes each)
                prev_off = offsets.get(id(node.prev), 0xFFFFFFFF)
                next_off = offsets.get(id(node.next), 0xFFFFFFFF)
                data += struct.pack("!II", prev_off, next_off)
                serialized_nodes.append(data)
            else:  # InternalNode
                data = node.serialize()
                # child offsets
                for child in node.children:
                    child_off = offsets[id(child)]
                    data += struct.pack("!I", child_off)
                serialized_nodes.append(data)
        # Header: number of nodes
        header = struct.pack("!I", len(nodes))
        body = b"".join(serialized_nodes)
        return header + body

    @staticmethod
    def deserialize(blob: bytes) -> "BPlusTree":
        offset = 0
        num_nodes = struct.unpack_from("!I", blob, offset)[0]
        offset += 4
        nodes = []
        # First pass: read node types and keys/values without resolving links
        for _ in range(num_nodes):
            node_type = struct.unpack_from("!B", blob, offset)[0]
            offset += 1
            if node_type == 0:  # leaf
                key_cnt = struct.unpack_from("!I", blob, offset)[0]
                offset += 4
                leaf = LeafNode()
                for _ in range(key_cnt):
                    k_len = struct.unpack_from("!I", blob, offset)[0]
                    offset += 4
                    k_bytes = blob[offset:offset + k_len]
                    offset += k_len
                    v_len = struct.unpack_from("!I", blob, offset)[0]
                    offset += 4
                    v_bytes = blob[offset:offset + v_len]
                    offset += v_len
                    leaf.keys.append(eval(k_bytes.decode('utf-8')))
                    leaf.values.append(eval(v_bytes.decode('utf-8')))
                prev_off, next_off = struct.unpack_from("!II", blob, offset)
                offset += 8
                leaf._prev_off = prev_off
                leaf._next_off = next_off
                nodes.append(leaf)
            else:  # internal
                key_cnt = struct.unpack_from("!I", blob, offset)[0]
                offset += 4
                internal = InternalNode()
                for _ in range(key_cnt):
                    k_len = struct.unpack_from("!I", blob, offset)[0]
                    offset += 4
                    k_bytes = blob[offset:offset + k_len]
                    offset += k_len
                    internal.keys.append(eval(k_bytes.decode('utf-8')))
                child_cnt = key_cnt + 1
                child_offsets = []
                for _ in range(child_cnt):
                    child_off = struct.unpack_from("!I", blob, offset)[0]
                    offset += 4
                    child_offsets.append(child_off)
                internal._child_offsets = child_offsets
                nodes.append(internal)
        # Second pass: resolve pointers
        for node in nodes:
            if isinstance(node, LeafNode):
                if node._prev_off != 0xFFFFFFFF:
                    node.prev = nodes[node._prev_off]
                if node._next_off != 0xFFFFFFFF:
                    node.next = nodes[node._next_off]
                del node._prev_off, node._next_off
            else:
                node.children = [nodes[i] for i in node._child_offsets]
                for child in node.children:
                    child.parent = node
                del node._child_offsets
        # Reattach root and leaf list pointers
        tree = BPlusTree()
        tree.root = nodes[0]
        # Find first leaf (traverse leftmost)
        cur = tree.root
        while isinstance(cur, InternalNode):
            cur = cur.children[0]
        tree.first_leaf = cur
        # Find last leaf
        while cur.next:
            cur = cur.next
        tree.last_leaf = cur
        return tree

# ---------------------------------------------------------------
# Test suite
import unittest

class TestBPlusTree(unittest.TestCase):
    def setUp(self):
        self.tree = BPlusTree(order=4)

    def test_leaf_split(self):
        # Insert enough keys to trigger a leaf split
        for i in range(1, 6):  # order=4 => max 3 entries per leaf
            self.tree.insert(i, f"v{i}")
        # After split, root should be internal with one key
        self.assertIsInstance(self.tree.root, InternalNode)
        self.assertEqual(len(self.tree.root.keys), 1)
        # Verify all keys are searchable
        for i in range(1, 6):
            self.assertEqual(self.tree.search(i), f"v{i}")

    def test_internal_split(self):
        # Insert enough keys to cause internal node split
        for i in range(1, 20):
            self.tree.insert(i, f"v{i}")
        # Height should be >1
        self.assertIsInstance(self.tree.root, InternalNode)
        # Verify random keys
        for i in [1, 5, 10, 15, 19]:
            self.assertEqual(self.tree.search(i), f"v{i}")

    def test_search_missing(self):
        self.tree.insert(10, "ten")
        self.assertIsNone(self.tree.search(5))
        self.assertIsNone(self.tree.search(15))

    def test_range_scan(self):
        for i in range(1, 11):
            self.tree.insert(i, i * 10)
        vals = self.tree.range_scan(3, 7)
        self.assertListEqual(vals, [30, 40, 50, 60, 70])
        # Scan across leaf boundaries
        vals = self.tree.range_scan(1, 10)
        self.assertListEqual(vals, [10,20,30,40,50,60,70,80,90,100])

    def test_serialize_deserialize(self):
        for i in range(1, 12):
            self.tree.insert(i, i)
        data = self.tree.serialize()
        new_tree = BPlusTree.deserialize(data)
        for i in range(1, 12):
            self.assertEqual(new_tree.search(i), i)
        # Verify range scan after deserialization
        self.assertListEqual(new_tree.range_scan(4, 9), [4,5,6,7,8,9])

if __name__ == "__main__":
    unittest.main()
