import copy

class RollbackUnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}
        self._snapshots = []

    def make_set(self, x):
        if x in self.parent:
            raise ValueError("Element already exists")
        self.parent[x] = x
        self.rank[x] = 0

    def find(self, x):
        if x not in self.parent:
            raise KeyError("Element not found")
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def union(self, x, y):
        rx = self.find(x)
        ry = self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            self.parent[rx] = ry
        elif self.rank[rx] > self.rank[ry]:
            self.parent[ry] = rx
        else:
            self.parent[ry] = rx
            self.rank[rx] += 1

    def save(self):
        # Store deep copies of the mutable state
        self._snapshots.append((copy.deepcopy(self.parent), copy.deepcopy(self.rank)))

    def restore(self):
        if not self._snapshots:
            raise RuntimeError("No saved state to restore")
        self.parent, self.rank = self._snapshots.pop()

# Tests
import unittest

class TestRollbackUnionFind(unittest.TestCase):
    def test_basic_operations(self):
        uf = RollbackUnionFind()
        uf.make_set('a')
        uf.make_set('b')
        uf.make_set('c')
        self.assertNotEqual(uf.find('a'), uf.find('b'))
        uf.union('a', 'b')
        self.assertEqual(uf.find('a'), uf.find('b'))
        self.assertNotEqual(uf.find('a'), uf.find('c'))
        uf.union('b', 'c')
        self.assertEqual(uf.find('a'), uf.find('c'))

    def test_rollback(self):
        uf = RollbackUnionFind()
        uf.make_set(1)
        uf.make_set(2)
        uf.make_set(3)
        uf.union(1, 2)
        uf.save()
        uf.union(2, 3)
        self.assertEqual(uf.find(1), uf.find(3))
        uf.restore()
        self.assertNotEqual(uf.find(1), uf.find(3))
        self.assertEqual(uf.find(1), uf.find(2))

    def test_nested_save_restore(self):
        uf = RollbackUnionFind()
        for i in range(5):
            uf.make_set(i)
        uf.union(0, 1)
        uf.save()  # state A
        uf.union(1, 2)
        uf.save()  # state B
        uf.union(2, 3)
        uf.save()  # state C
        uf.union(3, 4)
        # At this point all are connected
        self.assertEqual(uf.find(0), uf.find(4))
        # Restore to state C
        uf.restore()
        self.assertNotEqual(uf.find(0), uf.find(4))
        self.assertEqual(uf.find(0), uf.find(3))
        # Restore to state B
        uf.restore()
        self.assertNotEqual(uf.find(0), uf.find(3))
        self.assertEqual(uf.find(0), uf.find(2))
        # Restore to state A
        uf.restore()
        self.assertNotEqual(uf.find(0), uf.find(2))
        self.assertEqual(uf.find(0), uf.find(1))

if __name__ == '__main__':
    unittest.main()
