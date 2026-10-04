class DisjointSet:
    """Union by rank, no path compression, rollback through an operation log."""

    def __init__(self):
        self.parent, self.rank = {}, {}
        self.log, self.marks = [], []

    def make_set(self, x):
        if x not in self.parent:
            self.parent[x], self.rank[x] = x, 0
            self.log.append(("make", x))

    def find(self, x):
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        bumped = self.rank[rx] == self.rank[ry]
        if bumped:
            self.rank[rx] += 1
        self.log.append(("union", ry, rx, bumped))
        return True

    def save(self):
        self.marks.append(len(self.log))

    def restore(self):
        mark = self.marks.pop()
        while len(self.log) > mark:
            entry = self.log.pop()
            if entry[0] == "make":
                del self.parent[entry[1]], self.rank[entry[1]]
            else:
                _, child, root, bumped = entry
                self.parent[child] = child
                if bumped:
                    self.rank[root] -= 1
