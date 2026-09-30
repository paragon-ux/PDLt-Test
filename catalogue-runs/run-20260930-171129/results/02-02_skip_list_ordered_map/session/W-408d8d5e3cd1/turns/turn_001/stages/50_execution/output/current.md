# skiplist.py
import random
from typing import Any, List, Tuple, Optional

class SkipNode:
    __slots__ = ("key", "value", "forward", "level")
    def __init__(self, key: Any, value: Any, level: int):
        self.key = key
        self.value = value
        self.level = level
        self.forward: List[Optional[SkipNode]] = [None] * (level + 1)

class SkipListMap:
    MAX_LEVEL = 16
    P = 0.5

    def __init__(self):
        self.header = SkipNode(None, None, self.MAX_LEVEL)
        self.level = 0
        self.length = 0
        random.seed(0)  # deterministic for tests

    def _random_level(self) -> int:
        lvl = 0
        while random.random() < self.P and lvl < self.MAX_LEVEL:
            lvl += 1
        return lvl

    def insert(self, key: Any, value: Any) -> None:
        update: List[Optional[SkipNode]] = [None] * (self.MAX_LEVEL + 1)
        x = self.header
        for i in range(self.level, -1, -1):
            while x.forward[i] and x.forward[i].key < key:
                x = x.forward[i]
            update[i] = x
        x = x.forward[0]
        if x and x.key == key:
            x.value = value  # update existing
            return
        lvl = self._random_level()
        if lvl > self.level:
            for i in range(self.level + 1, lvl + 1):
                update[i] = self.header
            self.level = lvl
        new_node = SkipNode(key, value, lvl)
        for i in range(lvl + 1):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
        self.length += 1

    def search(self, key: Any) -> Optional[Any]:
        x = self.header
        for i in range(self.level, -1, -1):
            while x.forward[i] and x.forward[i].key < key:
                x = x.forward[i]
        x = x.forward[0]
        if x and x.key == key:
            return x.value
        return None

    def delete(self, key: Any) -> bool:
        update: List[Optional[SkipNode]] = [None] * (self.MAX_LEVEL + 1)
        x = self.header
        for i in range(self.level, -1, -1):
            while x.forward[i] and x.forward[i].key < key:
                x = x.forward[i]
            update[i] = x
        x = x.forward[0]
        if not x or x.key != key:
            return False
        for i in range(x.level + 1):
            if update[i].forward[i] != x:
                break
            update[i].forward[i] = x.forward[i]
        while self.level > 0 and self.header.forward[self.level] is None:
            self.level -= 1
        self.length -= 1
        return True

    def range_query(self, lo: Any, hi: Any) -> List[Tuple[Any, Any]]:
        result: List[Tuple[Any, Any]] = []
        x = self.header
        for i in range(self.level, -1, -1):
            while x.forward[i] and x.forward[i].key < lo:
                x = x.forward[i]
        x = x.forward[0]
        while x and x.key <= hi:
            result.append((x.key, x.value))
            x = x.forward[0]
        return result

# --- Test Suite ---
import unittest

class TestSkipListMap(unittest.TestCase):
    def setUp(self):
        self.map = SkipListMap()
        for k in range(1, 21):
            self.map.insert(k, str(k))

    def test_ordering(self):
        keys = [node.key for node in self._collect_nodes()]
        self.assertEqual(keys, list(range(1, 21)))

    def test_update(self):
        self.map.insert(5, "five")
        self.assertEqual(self.map.search(5), "five")

    def test_search(self):
        self.assertEqual(self.map.search(10), "10")
        self.assertIsNone(self.map.search(100))

    def test_delete(self):
        self.assertTrue(self.map.delete(10))
        self.assertIsNone(self.map.search(10))
        self.assertFalse(self.map.delete(100))

    def test_range_query(self):
        res = self.map.range_query(5, 10)
        expected = [(k, str(k)) for k in range(5, 11)]
        self.assertEqual(res, expected)

    def test_level_distribution(self):
        lvl_counts = [0] * (self.map.MAX_LEVEL + 1)
        for _ in range(1000):
            node = SkipNode(None, None, self.map._random_level())
            lvl_counts[node.level] += 1
        # Expected geometric distribution with p=0.5
        for lvl, cnt in enumerate(lvl_counts[:5]):  # check first few levels
            expected = 1000 * (0.5 ** (lvl + 1))
            self.assertTrue(abs(cnt - expected) < 100)  # tolerance

    def _collect_nodes(self):
        nodes = []
        x = self.map.header.forward[0]
        while x:
            nodes.append(x)
            x = x.forward[0]
        return nodes

if __name__ == "__main__":
    unittest.main()
