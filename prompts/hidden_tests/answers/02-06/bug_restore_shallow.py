# Wrong: save() keeps references to the live dicts, so restore() reverts nothing.
class DisjointSet:
    def __init__(self):
        self.parent, self.rank, self.stack = {}, {}, []

    def make_set(self, x):
        self.parent[x], self.rank[x] = x, 0

    def find(self, x):
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def union(self, x, y):
        a, b = self.find(x), self.find(y)
        if a != b:
            self.parent[b] = a

    def save(self):
        self.stack.append((self.parent, self.rank))

    def restore(self):
        self.parent, self.rank = self.stack.pop()
