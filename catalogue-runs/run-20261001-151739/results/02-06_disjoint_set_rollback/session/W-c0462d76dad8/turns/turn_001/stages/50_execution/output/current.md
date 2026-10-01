class UnionFindRollback:
    def __init__(self):
        self.parent = {}
        self.rank = {}
        self.history = []  # stack of (parent_snapshot, rank_snapshot)

    def make_set(self, x):
        if x in self.parent:
            raise ValueError("Element already exists")
        self.parent[x] = x
        self.rank[x] = 0

    def find(self, x):
        # No path compression to support rollback
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def union(self, x, y):
        xr = self.find(x)
        yr = self.find(y)
        if xr == yr:
            return
        # union by rank
        if self.rank[xr] < self.rank[yr]:
            xr, yr = yr, xr
        # attach yr under xr
        self.parent[yr] = xr
        if self.rank[xr] == self.rank[yr]:
            self.rank[xr] += 1

    def save(self):
        # snapshot copies of current state
        self.history.append((self.parent.copy(), self.rank.copy()))

    def restore(self):
        if not self.history:
            raise RuntimeError("No saved state to restore")
        parent_snapshot, rank_snapshot = self.history.pop()
        self.parent = parent_snapshot
        self.rank = rank_snapshot

# Unit tests
import unittest

class TestUnionFindRollback(unittest.TestCase):
    def setUp(self):
        self.uf = UnionFindRollback()
        for i in range(1, 6):
            self.uf.make_set(i)

    def test_basic_union_find(self):
        self.uf.union(1, 2)
        self.uf.union(3, 4)
        self.assertEqual(self.uf.find(1), self.uf.find(2))
        self.assertEqual(self.uf.find(3), self.uf.find(4))
        self.assertNotEqual(self.uf.find(1), self.uf.find(3))
        self.uf.union(2, 3)
        self.assertEqual(self.uf.find(1), self.uf.find(4))

    def test_rollback_single_save(self):
        self.uf.union(1, 2)
        self.uf.save()
        self.uf.union(2, 3)
        self.uf.union(4, 5)
        self.assertEqual(self.uf.find(1), self.uf.find(3))
        self.uf.restore()
        # after restore, 1 and 2 should still be united, but 3 separate
        self.assertEqual(self.uf.find(1), self.uf.find(2))
        self.assertNotEqual(self.uf.find(1), self.uf.find(3))
        self.assertNotEqual(self.uf.find(4), self.uf.find(5))

    def test_nested_save_restore(self):
        # initial unions
        self.uf.union(1, 2)
        self.uf.save()  # state A
        self.uf.union(2, 3)
        self.uf.save()  # state B
        self.uf.union(3, 4)
        self.uf.save()  # state C
        self.uf.union(4, 5)
        # verify all connected
        self.assertEqual(self.uf.find(1), self.uf.find(5))
        # restore to state C (undo last union)
        self.uf.restore()
        self.assertNotEqual(self.uf.find(1), self.uf.find(5))
        self.assertEqual(self.uf.find(1), self.uf.find(4))
        # restore to state B (undo union 3-4)
        self.uf.restore()
        self.assertNotEqual(self.uf.find(1), self.uf.find(4))
        self.assertEqual(self.uf.find(1), self.uf.find(3))
        # restore to state A (undo union 2-3)
        self.uf.restore()
        self.assertNotEqual(self.uf.find(1), self.uf.find(3))
        self.assertEqual(self.uf.find(1), self.uf.find(2))
        # no more saved states
        with self.assertRaises(RuntimeError):
            self.uf.restore()

if __name__ == "__main__":
    unittest.main()
