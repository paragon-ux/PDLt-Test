class RollbackUnionFind:
    """Disjoint set (union‑find) with union‑by‑rank and rollback support.
    No path compression is used so that snapshots can be restored exactly.
    """
    def __init__(self):
        # parent and rank dictionaries store the current state
        self.parent = {}
        self.rank = {}
        # stack of snapshots; each snapshot is a tuple (parent_copy, rank_copy)
        self._snapshots = []

    def make_set(self, x):
        """Create a new set containing element ``x``.
        If ``x`` already exists, it is left unchanged.
        """
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x):
        """Return the representative of the set containing ``x``.
        Follows parent links without path compression.
        """
        if x not in self.parent:
            raise KeyError(f"Element {x!r} not found in any set")
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def union(self, x, y):
        """Merge the sets containing ``x`` and ``y`` using union‑by‑rank.
        Returns ``True`` if a merge happened, ``False`` if they were already in the same set.
        """
        xr = self.find(x)
        yr = self.find(y)
        if xr == yr:
            return False
        # union by rank: attach lower‑rank tree under higher‑rank tree
        if self.rank[xr] < self.rank[yr]:
            self.parent[xr] = yr
        elif self.rank[xr] > self.rank[yr]:
            self.parent[yr] = xr
        else:
            self.parent[yr] = xr
            self.rank[xr] += 1
        return True

    def save(self):
        """Snapshot the current state. The snapshot can later be restored with :meth:`restore`."""
        # shallow copies are sufficient because values are immutable ints / strings
        self._snapshots.append((self.parent.copy(), self.rank.copy()))

    def restore(self):
        """Revert to the most recent snapshot saved by :meth:`save`.
        All changes performed after that snapshot (including further snapshots) are discarded.
        """
        if not self._snapshots:
            raise RuntimeError("No saved state to restore")
        parent_snapshot, rank_snapshot = self._snapshots.pop()
        self.parent = parent_snapshot
        self.rank = rank_snapshot

# --------------------- Unit Tests ---------------------
import unittest

class TestRollbackUnionFind(unittest.TestCase):
    def setUp(self):
        self.uf = RollbackUnionFind()
        for i in range(1, 7):
            self.uf.make_set(i)

    def test_basic_union_find(self):
        # Initially each element is its own representative
        for i in range(1, 7):
            self.assertEqual(self.uf.find(i), i)
        # Perform some unions
        self.uf.union(1, 2)
        self.uf.union(3, 4)
        self.uf.union(5, 6)
        # Check representatives
        rep12 = self.uf.find(1)
        self.assertEqual(rep12, self.uf.find(2))
        rep34 = self.uf.find(3)
        self.assertEqual(rep34, self.uf.find(4))
        rep56 = self.uf.find(5)
        self.assertEqual(rep56, self.uf.find(6))
        # Ensure different sets remain distinct
        self.assertNotEqual(rep12, rep34)
        self.assertNotEqual(rep12, rep56)
        self.assertNotEqual(rep34, rep56)

    def test_rollback_one_save(self):
        self.uf.union(1, 2)
        self.uf.union(3, 4)
        # Save state before further unions
        self.uf.save()
        self.uf.union(1, 3)
        self.uf.union(5, 6)
        # Verify merged components
        self.assertEqual(self.uf.find(1), self.uf.find(4))
        self.assertEqual(self.uf.find(5), self.uf.find(6))
        # Restore to saved state
        self.uf.restore()
        # After restore, 1 and 3 should be separate again
        self.assertNotEqual(self.uf.find(1), self.uf.find(3))
        # Union performed after save should be undone
        self.assertEqual(self.uf.find(5), 6)  # still separate because only union after save was undone
        # Original unions should persist
        self.assertEqual(self.uf.find(1), self.uf.find(2))
        self.assertEqual(self.uf.find(3), self.uf.find(4))

    def test_nested_save_restore(self):
        # Initial unions
        self.uf.union(1, 2)
        self.uf.save()                # Snapshot A
        self.uf.union(2, 3)
        self.uf.save()                # Snapshot B
        self.uf.union(3, 4)
        self.assertEqual(self.uf.find(1), self.uf.find(4))
        # Restore to Snapshot B
        self.uf.restore()
        self.assertEqual(self.uf.find(1), self.uf.find(3))
        self.assertNotEqual(self.uf.find(1), self.uf.find(4))
        # Restore to Snapshot A
        self.uf.restore()
        self.assertEqual(self.uf.find(1), self.uf.find(2))
        self.assertNotEqual(self.uf.find(1), self.uf.find(3))
        # No more snapshots -> restore should error
        with self.assertRaises(RuntimeError):
            self.uf.restore()

if __name__ == "__main__":
    unittest.main()
