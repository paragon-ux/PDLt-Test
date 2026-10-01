class RollbackUnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}
        self.history = []  # stack of snapshots

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
        # union by rank, record changes for rollback
        if self.rank[rx] < self.rank[ry]:
            self.parent[rx] = ry
        elif self.rank[rx] > self.rank[ry]:
            self.parent[ry] = rx
        else:
            self.parent[ry] = rx
            self.rank[rx] += 1

    def save(self):
        # snapshot current parent and rank dictionaries (shallow copy is enough)
        self.history.append((self.parent.copy(), self.rank.copy()))

    def restore(self):
        if not self.history:
            raise RuntimeError("No saved state to restore")
        self.parent, self.rank = self.history.pop()

# Test suite
if __name__ == "__main__":
    uf = RollbackUnionFind()
    # basic make_set and find
    for i in range(1, 6):
        uf.make_set(i)
    assert all(uf.find(i) == i for i in range(1, 6))
    # basic union operations
    uf.union(1, 2)
    uf.union(3, 4)
    assert uf.find(1) == uf.find(2)
    assert uf.find(3) == uf.find(4)
    assert uf.find(1) != uf.find(3)
    # rollback test
    uf.save()
    uf.union(2, 3)
    assert uf.find(1) == uf.find(4)
    uf.restore()
    assert uf.find(1) != uf.find(3)
    # nested save/restore test
    uf.save()
    uf.union(1, 3)
    uf.save()
    uf.union(5, 1)
    assert uf.find(5) == uf.find(2)
    uf.restore()
    assert uf.find(5) == 5  # 5 should be alone after inner restore
    uf.restore()
    assert uf.find(1) != uf.find(3)
    print("All tests passed.")
