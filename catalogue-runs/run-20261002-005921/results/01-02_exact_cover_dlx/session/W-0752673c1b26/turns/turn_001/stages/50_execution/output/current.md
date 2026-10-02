import itertools

def exact_covers():
    U = {1,2,3,4,5,6,7,8,9}
    sets = {
        'S1': {1,2,3},
        'S2': {4,5,6},
        'S3': {7,8,9},
        'S4': {1,4,7},
        'S5': {2,5,8},
        'S6': {3,6,9},
        'S7': {1,5,9},
        'S8': {2,6,7},
        'S9': {3,4,8},
    }
    # Build incidence matrix for Algorithm X
    # Each column is an element of U, each row is a set
    cols = list(U)
    rows = list(sets.keys())
    matrix = {r: {c: (c in sets[r]) for c in cols} for r in rows}

    # Dancing Links structures
    class Node:
        __slots__ = ('left','right','up','down','column','row')
        def __init__(self):
            self.left = self.right = self.up = self.down = self
            self.column = None
            self.row = None

    class ColumnNode(Node):
        __slots__ = ('size','name')
        def __init__(self, name):
            super().__init__()
            self.size = 0
            self.name = name
            self.column = self

    # Header
    header = ColumnNode('header')
    column_nodes = {}
    last = header
    for c in cols:
        col = ColumnNode(c)
        column_nodes[c] = col
        # link horizontally
        col.left = last
        col.right = header
        last.right = col
        header.left = col
        last = col

    # Add rows
    row_nodes = {}
    for r in rows:
        first = None
        prev = None
        for c in cols:
            if matrix[r][c]:
                col = column_nodes[c]
                node = Node()
                node.column = col
                node.row = r
                # vertical link
                node.up = col.up
                node.down = col
                col.up.down = node
                col.up = node
                col.size += 1
                # horizontal link within the row
                if first is None:
                    first = node
                else:
                    node.left = prev
                    node.right = first
                    prev.right = node
                    first.left = node
                prev = node
        row_nodes[r] = first

    solution = []
    results = []

    def cover(col):
        # remove column header
        col.right.left = col.left
        col.left.right = col.right
        # remove rows
        i = col.down
        while i != col:
            j = i.right
            while j != i:
                j.down.up = j.up
                j.up.down = j.down
                j.column.size -= 1
                j = j.right
            i = i.down

    def uncover(col):
        i = col.up
        while i != col:
            j = i.left
            while j != i:
                j.column.size += 1
                j.down.up = j
                j.up.down = j
                j = j.left
            i = i.up
        col.right.left = col
        col.left.right = col

    def search(k=0):
        if header.right == header:
            results.append(list(solution))
            return
        # choose column with smallest size
        c = header.right
        min_sz = c.size
        col = c
        while c != header:
            if c.size < min_sz:
                min_sz = c.size
                col = c
            c = c.right
        cover(col)
        r = col.down
        while r != col:
            solution.append(r.row)
            j = r.right
            while j != r:
                cover(j.column)
                j = j.right
            search(k+1)
            # backtrack
            solution.pop()
            j = r.left
            while j != r:
                uncover(j.column)
                j = j.left
            r = r.down
        uncover(col)

    search()
    return results

if __name__ == "__main__":
    sols = exact_covers()
    for sol in sols:
        print(sorted(sol))
    # Self‑contained test
    U = {1,2,3,4,5,6,7,8,9}
    sets = {
        'S1': {1,2,3},
        'S2': {4,5,6},
        'S3': {7,8,9},
        'S4': {1,4,7},
        'S5': {2,5,8},
        'S6': {3,6,9},
        'S7': {1,5,9},
        'S8': {2,6,7},
        'S9': {3,4,8},
    }
    for sol in sols:
        union = set()
        pairwise_ok = True
        for name in sol:
            s = sets[name]
            if union & s:
                pairwise_ok = False
                break
            union |= s
        assert union == U, f"Union does not cover U: {union}"
        assert pairwise_ok, f"Sets not pairwise disjoint in solution {sol}"
    print("All solutions verified.")
