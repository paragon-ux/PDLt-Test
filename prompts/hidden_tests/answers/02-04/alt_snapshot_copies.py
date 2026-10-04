# Correct with a different design: save() pushes full copies of the arrays.
class UnionFind:
    def __init__(self, size_hint=0):
        self.parent = {}
        self.rank = {}
        self.snapshots = []

    def make_set(self, x):
        self.parent.setdefault(x, x)
        self.rank.setdefault(x, 0)

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            if self.rank[ra] > self.rank[rb]:
                ra, rb = rb, ra
            self.parent[ra] = rb
            if self.rank[ra] == self.rank[rb]:
                self.rank[rb] += 1

    def save(self):
        self.snapshots.append((dict(self.parent), dict(self.rank)))

    def restore(self):
        self.parent, self.rank = self.snapshots.pop()
