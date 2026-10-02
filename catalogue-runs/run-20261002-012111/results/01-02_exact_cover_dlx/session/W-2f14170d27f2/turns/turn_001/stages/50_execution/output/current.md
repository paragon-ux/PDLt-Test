# Exact Cover Solver using Algorithm X (Dancing Links)
# Universe U = {1,2,3,4,5,6,7,8,9}
# Sets S1..S9 as defined in the task

from typing import List, Dict, Set

# Define the problem data
U: Set[int] = {1, 2, 3, 4, 5, 6, 7, 8, 9}
sets: Dict[str, Set[int]] = {
    "S1": {1, 2, 3},
    "S2": {4, 5, 6},
    "S3": {7, 8, 9},
    "S4": {1, 4, 7},
    "S5": {2, 5, 8},
    "S6": {3, 6, 9},
    "S7": {1, 5, 9},
    "S8": {2, 6, 7},
    "S9": {3, 4, 8},
}

# ---- Dancing Links implementation ----
class Node:
    __slots__ = ("left", "right", "up", "down", "column", "row_name")
    def __init__(self):
        self.left = self.right = self.up = self.down = self
        self.column = self  # type: ignore
        self.row_name = None

class ColumnNode(Node):
    __slots__ = ("size", "name")
    def __init__(self, name: str):
        super().__init__()
        self.size = 0
        self.name = name
        self.column = self

class DLX:
    def __init__(self, columns: List[str]):
        # Header node
        self.header = ColumnNode("header")
        self.column_lookup: Dict[str, ColumnNode] = {}
        last = self.header
        for name in columns:
            col = ColumnNode(name)
            self.column_lookup[name] = col
            # link horizontally
            col.left = last
            col.right = self.header
            last.right = col
            self.header.left = col
            last = col
        self.solution: List[Node] = []

    def add_row(self, row_name: str, cols: List[str]):
        first: Node = None  # type: ignore
        for col_name in cols:
            col = self.column_lookup[col_name]
            node = Node()
            node.column = col
            node.row_name = row_name
            # vertical link
            node.up = col.up
            node.down = col
            col.up.down = node
            col.up = node
            col.size += 1
            # horizontal link
            if first is None:
                first = node
                node.left = node.right = node
            else:
                node.left = first.left
                node.right = first
                first.left.right = node
                first.left = node
        # close circular list if only one node
        if first is not None and first.right is None:
            first.right = first.left = first

    def cover(self, col: ColumnNode):
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

    def uncover(self, col: ColumnNode):
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

    def search(self, k: int = 0):
        if self.header.right == self.header:
            # found a solution
            yield [node.row_name for node in self.solution]
            return
        # choose column with smallest size (heuristic)
        c = self.header.right
        min_size = c.size
        col = c
        while c != self.header:
            if c.size < min_size:
                min_size = c.size
                col = c
                if min_size == 0:
                    break
            c = c.right
        if min_size == 0:
            return  # dead end
        self.cover(col)
        r = col.down
        while r != col:
            self.solution.append(r)
            j = r.right
            while j != r:
                self.cover(j.column)
                j = j.right
            yield from self.search(k + 1)
            # backtrack
            self.solution.pop()
            j = r.left
            while j != r:
                self.uncover(j.column)
                j = j.left
            r = r.down
        self.uncover(col)

# Build DLX structure
column_names = [str(i) for i in sorted(U)]
DLX_instance = DLX(column_names)
for name, elems in sets.items():
    DLX_instance.add_row(name, [str(e) for e in elems])

# Enumerate all exact covers
all_covers: List[List[str]] = []
for sol in DLX_instance.search():
    all_covers.append(sol)

# ---- Test suite ----
def verify_cover(cover: List[str]) -> bool:
    covered: Set[int] = set()
    for set_name in cover:
        elems = sets[set_name]
        # ensure no overlap
        if covered & elems:
            return False
        covered |= elems
    return covered == U

assert all(verify_cover(c) for c in all_covers), "A returned cover does not exactly cover U"
print("Exact covers found:")
for idx, cov in enumerate(all_covers, 1):
    print(f"{idx}: {cov}")
