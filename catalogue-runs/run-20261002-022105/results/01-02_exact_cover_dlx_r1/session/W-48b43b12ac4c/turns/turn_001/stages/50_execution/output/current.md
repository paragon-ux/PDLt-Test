import json
from typing import List, Dict

# Define the universe and sets
U = {1, 2, 3, 4, 5, 6, 7, 8, 9}
sets = {
    'S1': {1, 2, 3},
    'S2': {4, 5, 6},
    'S3': {7, 8, 9},
    'S4': {1, 4, 7},
    'S5': {2, 5, 8},
    'S6': {3, 6, 9},
    'S7': {1, 5, 9},
    'S8': {2, 6, 7},
    'S9': {3, 4, 8},
}

# Build the exact cover matrix: each column is an element of U, each row a set
def build_matrix(sets: Dict[str, set], universe: set):
    col_index = {elem: i for i, elem in enumerate(sorted(universe))}
    rows = []
    row_names = []
    for name, elems in sets.items():
        row = [0] * len(universe)
        for e in elems:
            row[col_index[e]] = 1
        rows.append(row)
        row_names.append(name)
    return rows, row_names

# Dancing Links implementation (Knuth's Algorithm X)
class DLXNode:
    def __init__(self):
        self.left = self.right = self.up = self.down = self
        self.column = None
        self.name = None

class ColumnNode(DLXNode):
    def __init__(self, name):
        super().__init__()
        self.size = 0
        self.name = name
        self.column = self

def cover(column: ColumnNode):
    column.right.left = column.left
    column.left.right = column.right
    i = column.down
    while i is not column:
        j = i.right
        while j is not i:
            j.down.up = j.up
            j.up.down = j.down
            j.column.size -= 1
            j = j.right
        i = i.down

def uncover(column: ColumnNode):
    i = column.up
    while i is not column:
        j = i.left
        while j is not i:
            j.column.size += 1
            j.down.up = j
            j.up.down = j
            j = j.left
        i = i.up
    column.right.left = column
    column.left.right = column

def select_column(root: ColumnNode):
    # Choose column with smallest size (heuristic)
    min_size = float('inf')
    chosen = None
    j = root.right
    while j is not root:
        if j.size < min_size:
            min_size = j.size
            chosen = j
        j = j.right
    return chosen

def search(k: int, solution: List[DLXNode], root: ColumnNode, results: List[List[str]]):
    if root.right is root:
        # Found a solution
        results.append([node.name for node in solution])
        return
    column = select_column(root)
    if column.size == 0:
        return  # dead end
    cover(column)
    r = column.down
    while r is not column:
        solution.append(r)
        j = r.right
        while j is not r:
            cover(j.column)
            j = j.right
        search(k+1, solution, root, results)
        # backtrack
        solution.pop()
        j = r.left
        while j is not r:
            uncover(j.column)
            j = j.left
        r = r.down
    uncover(column)

def build_dlx(rows: List[List[int]], row_names: List[str]):
    # Header root
    root = ColumnNode('root')
    # Create column headers
    cols = []
    for i in range(len(rows[0])):
        col = ColumnNode(str(i))
        cols.append(col)
        # link into header list
        col.right = root
        col.left = root.left
        root.left.right = col
        root.left = col
    # Link rows
    for r_idx, row in enumerate(rows):
        prev = None
        for c_idx, val in enumerate(row):
            if val:
                col = cols[c_idx]
                node = DLXNode()
                node.column = col
                node.name = row_names[r_idx]
                # vertical link
                node.down = col
                node.up = col.up
                col.up.down = node
                col.up = node
                col.size += 1
                # horizontal link
                if prev is None:
                    prev = node
                    node.right = node.left = node
                else:
                    node.right = prev
                    node.left = prev.left
                    prev.left.right = node
                    prev.left = node
        # ensure circular for each row (if any nodes were added)
        if prev is not None:
            first = prev.right
            first.left = prev
            prev.right = first
    return root

def find_exact_covers():
    rows, row_names = build_matrix(sets, U)
    root = build_dlx(rows, row_names)
    results = []
    search(0, [], root, results)
    # Convert set names to actual set collections
    covers = []
    for sol in results:
        cover = [s for s in sol]
        covers.append(cover)
    return covers

if __name__ == "__main__":
    covers = find_exact_covers()
    # Verify each cover covers U exactly once
    def verify(cover):
        covered = set()
        for name in cover:
            covered.update(sets[name])
        return covered == U and all(len(set.intersection(*[sets[n] for n in cover])) == 0 for _ in cover)
    verified = [c for c in covers if verify(c)]
    # Prepare witness
    witness = {
        "polarity": "positive",
        "data": {
            "exact_covers": verified
        }
    }
    print("WITNESS: " + json.dumps(witness))

[host] Witness values are written into the program, not computed; unverified.

```json
{
  "files": [],
  "reconciliation": [],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "data": {
      "exact_covers": [
        [
          "S1",
          "S2",
          "S3"
        ],
        [
          "S4",
          "S5",
          "S6"
        ],
        [
          "S7",
          "S8",
          "S9"
        ]
      ]
    },
    "provisional": true
  }
}
```
