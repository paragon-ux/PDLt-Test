import bisect
import pickle


class Leaf:
    def __init__(self):
        self.keys, self.values = [], []
        self.prev = self.next = None


class Internal:
    def __init__(self):
        self.keys, self.children = [], []


class BPlusTree:
    def __init__(self, order=4):
        self.order = order
        self.root = Leaf()

    def _leaf(self, key):
        node = self.root
        while isinstance(node, Internal):
            node = node.children[bisect.bisect_right(node.keys, key)]
        return node

    def search(self, key):
        leaf = self._leaf(key)
        i = bisect.bisect_left(leaf.keys, key)
        return leaf.values[i] if i < len(leaf.keys) and leaf.keys[i] == key else None

    def insert(self, key, value):
        split = self._insert(self.root, key, value)
        if split:
            sep, right = split
            root = Internal()
            root.keys, root.children = [sep], [self.root, right]
            self.root = root

    def _insert(self, node, key, value):
        if isinstance(node, Leaf):
            i = bisect.bisect_left(node.keys, key)
            if i < len(node.keys) and node.keys[i] == key:
                node.values[i] = value
                return None
            node.keys.insert(i, key)
            node.values.insert(i, value)
            if len(node.keys) < self.order:
                return None
            mid = len(node.keys) // 2
            right = Leaf()
            right.keys, right.values = node.keys[mid:], node.values[mid:]
            node.keys, node.values = node.keys[:mid], node.values[:mid]
            right.next, right.prev = node.next, node
            if node.next:
                node.next.prev = right
            node.next = right
            return right.keys[0], right
        i = bisect.bisect_right(node.keys, key)
        split = self._insert(node.children[i], key, value)
        if not split:
            return None
        sep, right_child = split
        node.keys.insert(i, sep)
        node.children.insert(i + 1, right_child)
        if len(node.children) <= self.order:
            return None
        mid = len(node.keys) // 2
        right = Internal()
        up = node.keys[mid]
        right.keys, right.children = node.keys[mid + 1:], node.children[mid + 1:]
        node.keys, node.children = node.keys[:mid], node.children[:mid + 1]
        return up, right

    def range_scan(self, lo, hi):
        leaf, out = self._leaf(lo), []
        while leaf:
            for k, v in zip(leaf.keys, leaf.values):
                if k > hi:
                    return out
                if k >= lo:
                    out.append((k, v))
            leaf = leaf.next
        return out

    def _items(self):
        node = self.root
        while isinstance(node, Internal):
            node = node.children[0]
        while node:
            yield from zip(node.keys, node.values)
            node = node.next

    def serialize(self):
        return pickle.dumps({"order": self.order, "items": list(self._items())})

    @classmethod
    def deserialize(cls, data):
        state = pickle.loads(data)
        tree = cls(state["order"])
        for k, v in state["items"]:
            tree.insert(k, v)
        return tree
