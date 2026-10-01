```python
import random
import unittest
from typing import Any, List, Optional, Tuple

class SkipListNode:
    __slots__ = ('key', 'value', 'forward')
    def __init__(self, key: Any = None, value: Any = None, level: int = 0):
        self.key = key
        self.value = value
        self.forward: List[Optional[SkipListNode]] = [None] * (level + 1)

class SkipList:
    MAX_LEVEL = 16
    P = 0.5
    def __init__(self):
        self.head = SkipListNode(level=self.MAX_LEVEL)
        self.level = 0
        self.size = 0

    def random_level(self) -> int:
        lvl = 0
        while random.random() < self.P and lvl < self.MAX_LEVEL:
            lvl += 1
        return lvl

    def insert(self, key: Any, value: Any) -> None:
        update = [None] * (self.MAX_LEVEL + 1)
        current = self.head
        # Find place to insert
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current
        # Move to possible existing node
        current = current.forward[0]
        if current and current.key == key:
            current.value = value  # update existing
            return
        lvl = self.random_level()
        if lvl > self.level:
            for i in range(self.level + 1, lvl + 1):
                update[i] = self.head
            self.level = lvl
        new_node = SkipListNode(key, value, lvl)
        for i in range(lvl + 1):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
        self.size += 1

    def search(self, key: Any) -> Optional[Any]:
        current = self.head
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
        current = current.forward[0]
        if current and current.key == key:
            return current.value
        return None

    def delete(self, key: Any) -> bool:
        update = [None] * (self.MAX_LEVEL + 1)
        current = self.head
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current
        current = current.forward[0]
        if current and current.key == key:
            for i in range(self.level + 1):
                if update[i].forward[i] != current:
                    break
                update[i].forward[i] = current.forward[i]
            while self.level > 0 and self.head.forward[self.level] is None:
                self.level -= 1
            self.size -= 1
            return True
        return False

    def range_query(self, lo: Any, hi: Any) -> List[Tuple[Any, Any]]:
        result: List[Tuple[Any, Any]] = []
        current = self.head
        # Find first node >= lo
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < lo:
                current = current.forward[i]
        current = current.forward[0]
        while current and current.key <= hi:
            if current.key >= lo:
                result.append((current.key, current.value))
            current = current.forward[0]
        return result

class TestSkipList(unittest.TestCase):
    def setUp(self):
        self.skiplist = SkipList()
        self.keys = list(range(1, 101))
        random.shuffle(self.keys)
        for k in self.keys:
            self.skiplist.insert(k, k * 10)

    def test_search(self):
        for k in self.keys:
            self.assertEqual(self.skiplist.search(k), k * 10)
        self.assertIsNone(self.skiplist.search(0))
        self.assertIsNone(self.skiplist.search(101))

    def test_delete(self):
        to_delete = self.keys[:20]
        for k in to_delete:
            self.assertTrue(self.skiplist.delete(k))
        for k in to_delete:
            self.assertIsNone(self.skiplist.search(k))
        # Ensure remaining keys are still searchable
        for k in self.keys[20:]:
            self.assertEqual(self.skiplist.search(k), k * 10)

    def test_ordering_invariants(self):        # After deletions, iterate through level 0 list and verify ordering
        prev_key = None
        node = self.skiplist.head.forward[0]
        while node:
            if prev_key is not None:
                self.assertLess(prev_key, node.key)
            prev_key = node.key
            node = node.forward[0]

    def test_range_query(self):
        # Simple range
        lo, hi = 20, 30
        expected = [(k, k * 10) for k in range(lo, hi + 1) if k in self.keys]
        result = self.skiplist.range_query(lo, hi)
        self.assertCountEqual(result, expected)
        # Edge cases
        self.assertEqual(self.skiplist.range_query(0, 0), [])
        self.assertEqual(self.skiplist.range_query(101, 200), [])
        # Full range
        full = self.skiplist.range_query(1, 100)
        self.assertCountEqual(full, [(k, k * 10) for k in self.keys])

    def test_level_distribution(self):
        # Perform 1000 insertions and record levels
        levels = []
        for i in range(1000):
            lvl = self.skiplist.random_level()
            levels.append(lvl)
        # Verify that distribution roughly follows 0.5 probability per level
        from collections import Counter
        cnt = Counter(levels)
        total = sum(cnt.values())
        for lvl in range(1, 5):  # check first few levels
            prob = cnt[lvl] / total
            self.assertTrue(0.2 <= prob <= 0.8)  # loosely bound

if __name__ == "__main__":
    unittest.main()
```
