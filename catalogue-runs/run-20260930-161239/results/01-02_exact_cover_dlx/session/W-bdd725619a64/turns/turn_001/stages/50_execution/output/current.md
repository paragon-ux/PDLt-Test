import sys
from typing import List, Dict

# Define universe and subsets
U = {1,2,3,4,5,6,7,8,9}
subsets = {
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

# Build exact-cover matrix rows -> columns
# Columns are elements 1..9
cols = list(range(1,10))
rows = []
row_names = []
for name, elems in subsets.items():
    rows.append([1 if c in elems else 0 for c in cols])
    row_names.append(name)

# Dancing Links implementation (simplified for this small problem)
class Node:
    def __init__(self, row=None, col=None):
        self.left = self.right = self.up = self.down = self
        self.column = col
        self.row = row

class ColumnNode(Node):
    def __init__(self, name):
        super().__init__(row=None, col=self)
        self.size = 0
        self.name = name

# Build DLX structure
header = ColumnNode('header')
column_nodes = []
prev = header
for c in cols:
    col_node = ColumnNode(c)
    column_nodes.append(col_node)
    # link horizontally
    prev.right = col_node
    col_node.left = prev
    prev = col_node
# close loop
prev.right = header
header.left = prev

# add rows
row_nodes = []
for r_idx, row in enumerate(rows):
    first = None
    for c_idx, val in enumerate(row):
        if val:
            col_node = column_nodes[c_idx]
            node = Node(row=r_idx, col=col_node)
            # vertical link
            node.down = col_node
            node.up = col_node.up
            col_node.up.down = node
            col_node.up = node
            col_node.size += 1
            # horizontal link
            if first is None:
                first = node
                node.right = node.left = node
            else:
                node.right = first
                node.left = first.left
                first.left.right = node
                first.left = node
    row_nodes.append(first)

solution_indices: List[int] = []
solutions: List[List[str]] = []

def cover(col: ColumnNode):
    col.right.left = col.left
    col.left.right = col.right
    i = col.down
    while i != col:
        j = i.right
        while j != i:
            j.down.up = j.up
            j.up.down = j.down
            j.column.size -= 1
            j = j.right
        i = i.down

def uncover(col: ColumnNode):
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

def search(k: int):
    if header.right == header:
        # found solution
        sol = [row_names[idx] for idx in solution_indices]
        solutions.append(sol)
        return
    # choose column with minimal size
    c = header.right
    min_size = c.size
    col = c
    while c != header:
        if c.size < min_size:
            min_size = c.size
            col = c
        c = c.right
    if col.size == 0:
        return
    cover(col)
    r = col.down
    while r != col:
        solution_indices.append(r.row)
        j = r.right
        while j != r:
            cover(j.column)
            j = j.right
        search(k+1)
        # backtrack
        solution_indices.pop()
        j = r.left
        while j != r:
            uncover(j.column)
            j = j.left
        r = r.down
    uncover(col)

search(0)

# Verify solutions
all_ok = True
for sol in solutions:
    covered = set()
    for name in sol:
        covered.update(subsets[name])
    if covered != U:
        all_ok = False
        break
print('/'.join([str(s) for s in solutions]))
print('All solutions verified:', all_ok)
# Emit witness
witness = {
    "polarity": "positive",
    "evidence": {"path": "execution://witness"},
    "data": {"solutions": solutions}
}
print('WITNESS:', witness)

```json
{
  "files": [
    {
      "filename": "dlx_exact_cover.py",
      "satisfies": [
        "R1"
      ],
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": null
      }
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "def search(k: int):"
      }
    }
  ],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "evidence": {
      "path": "execution://witness"
    },
    "data": {
      "solutions": [
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
    "provisional": false
  }
}
```
