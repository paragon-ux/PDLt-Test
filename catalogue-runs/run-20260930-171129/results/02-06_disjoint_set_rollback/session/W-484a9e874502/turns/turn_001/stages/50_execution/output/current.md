class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}
        self.history = []  # stack of (action, data)
        self.save_markers = []  # positions of save points in history

    def make_set(self, x):
        if x in self.parent:
            raise ValueError("Element already exists")
        self.parent[x] = x
        self.rank[x] = 0
        # record creation for rollback
        self.history.append(("make_set", x))

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
        # ensure rx has not higher rank than ry
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        # now rank[rx] >= rank[ry]
        # record state before change for rollback
        self.history.append(("union", (ry, self.parent[ry], rx, self.rank[rx])))
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

    def save(self):
        # marker is the current length of history
        self.save_markers.append(len(self.history))
        # also push a marker entry so that restore knows where to stop
        self.history.append(("save_marker", None))

    def restore(self):
        if not self.save_markers:
            raise RuntimeError("No saved state to restore")
        marker = self.save_markers.pop()
        # pop until we remove the saved marker entry
        while self.history:
            action, data = self.history.pop()
            if action == "save_marker":
                break
            if action == "make_set":
                # undo creation
                del self.parent[data]
                del self.rank[data]
            elif action == "union":
                ry, old_parent, rx, old_rank = data
                self.parent[ry] = old_parent
                self.rank[rx] = old_rank
        # truncate any excess history beyond marker (should be empty now)
        self.history = self.history[:marker]

# Unit tests
if __name__ == "__main__":
    uf = UnionFind()
    for i in range(1, 6):
        uf.make_set(i)
    # basic unions
    uf.union(1, 2)
    uf.union(3, 4)
    assert uf.find(1) == uf.find(2)
    assert uf.find(3) == uf.find(4)
    assert uf.find(1) != uf.find(3)
    # Save state
    uf.save()
    uf.union(2, 3)  # merges the two components
    assert uf.find(1) == uf.find(4)
    # Restore should revert the merge
    uf.restore()
    assert uf.find(1) != uf.find(3)
    # Nested save/restore
    uf.save()
    uf.union(1, 5)
    uf.save()
    uf.union(5, 3)
    assert uf.find(1) == uf.find(3)
    uf.restore()  # undo second union
    assert uf.find(1) != uf.find(3)
    uf.restore()  # undo first union
    assert uf.find(1) != uf.find(5)
    print("All tests passed.")
