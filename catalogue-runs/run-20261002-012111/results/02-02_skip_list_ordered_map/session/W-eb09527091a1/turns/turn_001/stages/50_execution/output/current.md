import random
import unittest

class SkipListNode:
    __slots__ = ('key', 'value', 'forward')
    def __init__(self, key=None, value=None, level=0):
        self.key = key
        self.value = value
        self.forward = [None] * (level + 1)

class SkipListMap:
    MAX_LEVEL = 16
    P = 0.5

    def __init__(self):
        self.header = SkipListNode(level=self.MAX_LEVEL)
        self.level = 0
        self.length = 0

    def random_level(self):
        lvl = 0
        while random.random() < self.P and lvl < self.MAX_LEVEL:
            lvl += 1
        return lvl

    def insert(self, key, value):
        update = [None] * (self.MAX_LEVEL + 1)
        x = self.header
        for i in range(self.level, -1, -1):
            while x.forward[i] and x.forward[i].key < key:
                x = x.forward[i]
            update[i] = x
        x = x.forward[0]
        if x and x.key == key:
            x.value = value
            return
        lvl = self.random_level()
        if lvl > self.level:
            for i in range(self.level + 1, lvl + 1):
                update[i] = self.header
            self.level = lvl
        new_node = SkipListNode(key, value, lvl)
        for i in range(lvl + 1):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
        self.length += 1

    def search(self, key):
        x = self.header
        for i in range(self.level, -1, -1):
            while x.forward[i] and x.forward[i].key < key:
                x = x.forward[i]
        x = x.forward[0]
        if x and x.key == key:
            return x.value
        return None

    def delete(self, key):
        update = [None] * (self.MAX_LEVEL + 1)
        x = self.header
        for i in range(self.level, -1, -1):
            while x.forward[i] and x.forward[i].key < key:
                x = x.forward[i]
            update[i] = x
        x = x.forward[0]
        if not x or x.key != key:
            return
        for i in range(self.level + 1):
            if update[i].forward[i] != x:
                break
            update[i].forward[i] = x.forward[i]
        while self.level > 0 and self.header.forward[self.level] is None:
            self.level -= 1
        self.length -= 1

    def range_query(self, lo, hi):
        result = []
        x = self.header
        for i in range(self.level, -1, -1):
            while x.forward[i] and x.forward[i].key < lo:
                x = x.forward[i]
        x = x.forward[0]
        while x and x.key <= hi:
            if x.key >= lo:
                result.append((x.key, x.value))
            x = x.forward[0]
        return result

class TestSkipListMap(unittest.TestCase):
    def setUp(self):
        random.seed(0)
        self.skip = SkipListMap()

    def test_insert_search(self):
        for k in range(10):
            self.skip.insert(k, k*10)
        for k in range(10):
            self.assertEqual(self.skip.search(k), k*10)
        self.assertIsNone(self.skip.search(100))

    def test_update(self):
        self.skip.insert(5, 50)
        self.assertEqual(self.skip.search(5), 50)
        self.skip.insert(5, 55)
        self.assertEqual(self.skip.search(5), 55)

    def test_delete(self):
        for k in range(5):
            self.skip.insert(k, k)
        self.skip.delete(2)
        self.assertIsNone(self.skip.search(2))
        for k in [0,1,3,4]:
            self.assertEqual(self.skip.search(k), k)
        self.skip.delete(0)
        self.assertIsNone(self.skip.search(0))

    def test_range_query(self):
        for k in range(20):
            self.skip.insert(k, k*k)
        res = self.skip.range_query(5, 10)
        expected = [(k, k*k) for k in range(5, 11)]
        self.assertEqual(res, expected)

    def test_level_distribution(self):
        levels = [0]* (self.skip.MAX_LEVEL+1)
        for i in range(1000):
            lvl = self.skip.random_level()
            levels[lvl] += 1
        # Expected geometric distribution; just check no level dominates
        self.assertTrue(max(levels[1:]) < 400)

if __name__ == '__main__':
    unittest.main()
