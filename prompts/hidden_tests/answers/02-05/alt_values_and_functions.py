# Correct with a different interface: range_scan returns values, the bounds are
# inclusive, and serialization is a pair of module functions over a JSON payload.
import bisect
import json


class Node:
    def __init__(self, leaf):
        self.leaf, self.keys, self.kids, self.vals, self.next = leaf, [], [], [], None


class BTree:
    def __init__(self, max_children=4):
        self.m = max_children
        self.root = Node(True)

    def search(self, key):
        n = self.root
        while not n.leaf:
            n = n.kids[bisect.bisect_right(n.keys, key)]
        i = bisect.bisect_left(n.keys, key)
        if i < len(n.keys) and n.keys[i] == key:
            return n.vals[i]
        raise KeyError(key)

    def insert(self, key, value):
        res = self._ins(self.root, key, value)
        if res:
            r = Node(False)
            r.keys, r.kids = [res[0]], [self.root, res[1]]
            self.root = r

    def _ins(self, n, key, value):
        if n.leaf:
            i = bisect.bisect_left(n.keys, key)
            if i < len(n.keys) and n.keys[i] == key:
                n.vals[i] = value
                return None
            n.keys.insert(i, key)
            n.vals.insert(i, value)
            if len(n.keys) < self.m:
                return None
            h = len(n.keys) // 2
            s = Node(True)
            s.keys, s.vals, n.keys, n.vals = n.keys[h:], n.vals[h:], n.keys[:h], n.vals[:h]
            s.next, n.next = n.next, s
            return s.keys[0], s
        i = bisect.bisect_right(n.keys, key)
        res = self._ins(n.kids[i], key, value)
        if not res:
            return None
        n.keys.insert(i, res[0])
        n.kids.insert(i + 1, res[1])
        if len(n.kids) <= self.m:
            return None
        h = len(n.keys) // 2
        s = Node(False)
        up = n.keys[h]
        s.keys, s.kids, n.keys, n.kids = n.keys[h + 1:], n.kids[h + 1:], n.keys[:h], n.kids[:h + 1]
        return up, s

    def range_scan(self, lo, hi):
        n = self.root
        while not n.leaf:
            n = n.kids[bisect.bisect_right(n.keys, lo)]
        out = []
        while n:
            for k, v in zip(n.keys, n.vals):
                if lo <= k <= hi:
                    out.append(v)
                elif k > hi:
                    return out
            n = n.next
        return out


def serialize(tree):
    n = tree.root
    while not n.leaf:
        n = n.kids[0]
    items = []
    while n:
        items += list(zip(n.keys, n.vals))
        n = n.next
    return json.dumps({"m": tree.m, "items": items}).encode()


def deserialize(data):
    state = json.loads(data.decode())
    tree = BTree(state["m"])
    for k, v in state["items"]:
        tree.insert(k, v)
    return tree
