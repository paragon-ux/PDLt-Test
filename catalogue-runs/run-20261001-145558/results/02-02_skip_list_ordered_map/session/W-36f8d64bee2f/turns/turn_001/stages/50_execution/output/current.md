class Node:
    __slots__ = ('key', 'value', 'forward')
    def __init__(self, key, value, level):
        self.key = key
        self.value = value
        self.forward = [None] * level

class SkipList:
    MAX_LEVEL = 16
    P = 0.5

    def __init__(self):
        self.head = Node(None, None, self.MAX_LEVEL)
        self.level = 1
        self.size = 0

    def random_level(self):
        lvl = 1
        import random
        while random.random() < self.P and lvl < self.MAX_LEVEL:
            lvl += 1
        return lvl

    def insert(self, key, value):
        update = [None] * self.MAX_LEVEL
        current = self.head
        for i in reversed(range(self.level)):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current
        # check if key exists
        candidate = current.forward[0]
        if candidate and candidate.key == key:
            candidate.value = value
            return
        lvl = self.random_level()
        if lvl > self.level:
            for i in range(self.level, lvl):
                update[i] = self.head
            self.level = lvl
        new_node = Node(key, value, lvl)
        for i in range(lvl):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
        self.size += 1

    def search(self, key):
        current = self.head
        for i in reversed(range(self.level)):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
        current = current.forward[0]
        if current and current.key == key:
            return current.value
        return None

    def delete(self, key):
        update = [None] * self.MAX_LEVEL
        current = self.head
        for i in reversed(range(self.level)):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current
        target = current.forward[0]
        if target and target.key == key:
            for i in range(self.level):
                if update[i].forward[i] != target:
                    break
                update[i].forward[i] = target.forward[i]
            while self.level > 1 and self.head.forward[self.level-1] is None:
                self.level -= 1
            self.size -= 1

    def range_query(self, lo, hi):
        result = []
        current = self.head
        for i in reversed(range(self.level)):
            while current.forward[i] and current.forward[i].key < lo:
                current = current.forward[i]
        current = current.forward[0]
        while current and current.key <= hi:
            if current.key >= lo:
                result.append((current.key, current.value))
            current = current.forward[0]
        return result

# Test suite
import unittest
import random

class TestSkipList(unittest.TestCase):
    def setUp(self):
        self.sl = SkipList()
    def test_ordering(self):
        keys = list(range(100))
        random.shuffle(keys)
        for k in keys:
            self.sl.insert(k, str(k))
        # iterate through level 0
        current = self.sl.head.forward[0]
        sorted_keys = []
        while current:
            sorted_keys.append(current.key)
            current = current.forward[0]
        self.assertEqual(sorted_keys, sorted(keys))
    def test_random_level_distribution(self):
        levels = []
        for _ in range(1000):
            levels.append(self.sl.random_level())
        # Expected geometric distribution with p=0.5
        from collections import Counter
        cnt = Counter(levels)
        total = sum(cnt.values())
        for lvl in range(1, 5):  # check first few levels
            expected = (0.5 ** (lvl - 1)) * 0.5 * total
            observed = cnt.get(lvl, 0)
            # allow 20% tolerance
            self.assertTrue(abs(observed - expected) / expected < 0.2)
    def test_range_query(self):
        data = {5: 'a', 10: 'b', 15: 'c', 20: 'd'}
        for k, v in data.items():
            self.sl.insert(k, v)
        result = self.sl.range_query(7, 18)
        expected = [(10, 'b'), (15, 'c')]
        self.assertEqual(result, expected)
        # full range
        result_all = self.sl.range_query(0, 100)
        self.assertEqual(result_all, sorted(data.items()))
        # empty range
        self.assertEqual(self.sl.range_query(30, 40), [])

if __name__ == '__main__':
    unittest.main()
