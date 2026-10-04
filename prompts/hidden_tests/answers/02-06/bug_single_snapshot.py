# Wrong: keeps only one saved state, so nested save/restore loses the outer level.
class DSU:
    def __init__(self):
        self.parent, self.rank, self.saved = {}, {}, None

    def make_set(self, x):
        self.parent[x], self.rank[x] = x, 0

    def find(self, x):
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def union(self, x, y):
        a, b = self.find(x), self.find(y)
        if a == b:
            return
        if self.rank[a] < self.rank[b]:
            a, b = b, a
        self.parent[b] = a
        if self.rank[a] == self.rank[b]:
            self.rank[a] += 1

    def save(self):
        self.saved = (dict(self.parent), dict(self.rank))

    def restore(self):
        if self.saved:
            self.parent, self.rank = dict(self.saved[0]), dict(self.saved[1])
