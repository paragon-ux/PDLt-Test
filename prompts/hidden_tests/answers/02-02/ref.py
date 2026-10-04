import random

MAX_LEVEL = 16


class _Node:
    __slots__ = ("key", "value", "forward")

    def __init__(self, key, value, level):
        self.key, self.value = key, value
        self.forward = [None] * level


class SkipList:
    def __init__(self, p=0.5, seed=None):
        self.p = p
        self.rng = random.Random(seed)
        self.head = _Node(None, None, MAX_LEVEL)
        self.level = 1

    def _random_level(self):
        level = 1
        while level < MAX_LEVEL and self.rng.random() < self.p:
            level += 1
        return level

    def _path(self, key):
        update, node = [self.head] * MAX_LEVEL, self.head
        for i in range(self.level - 1, -1, -1):
            while node.forward[i] is not None and node.forward[i].key < key:
                node = node.forward[i]
            update[i] = node
        return update, node.forward[0]

    def insert(self, key, value):
        update, nxt = self._path(key)
        if nxt is not None and nxt.key == key:
            nxt.value = value
            return
        level = self._random_level()
        self.level = max(self.level, level)
        node = _Node(key, value, level)
        for i in range(level):
            node.forward[i] = update[i].forward[i]
            update[i].forward[i] = node

    def search(self, key):
        _, nxt = self._path(key)
        return nxt.value if nxt is not None and nxt.key == key else None

    def delete(self, key):
        update, nxt = self._path(key)
        if nxt is None or nxt.key != key:
            return False
        for i in range(len(nxt.forward)):
            if update[i].forward[i] is nxt:
                update[i].forward[i] = nxt.forward[i]
        return True

    def range_query(self, lo, hi):
        _, node = self._path(lo)
        out = []
        while node is not None and node.key <= hi:
            out.append((node.key, node.value))
            node = node.forward[0]
        return out
