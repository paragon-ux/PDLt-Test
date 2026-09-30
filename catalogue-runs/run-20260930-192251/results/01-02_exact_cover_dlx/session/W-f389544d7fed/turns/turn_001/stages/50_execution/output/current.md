#!/usr/bin/env python3
from typing import List

U = set(range(1, 10))
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

# Build exact‑cover matrix
elements = list(U)
set_names = list(sets.keys())
matrix = [[1 if e in sets[s] else 0 for s in set_names] for e in elements]

class Node:
    def __init__(self):
        self.left = self.right = self.up = self.down = self
        self.column = None
        self.row_name = None

class ColumnNode(Node):
    def __init__(self, name):
        super().__init__()
        self.size = 0
        self.name = name

def build_links():
    header = ColumnNode('header')
    column_nodes = {}
    # column headers for each element
    for name in elements:
        col = ColumnNode(name)
        column_nodes[name] = col
        # link horizontally
        col.right = header
        col.left = header.left
        header.left.right = col
        header.left = col
    # data nodes per set
    for r, set_name in enumerate(set_names):
        first = None
        for c, elem in enumerate(elements):
            if matrix[c][r]:
                col = column_nodes[elem]
                node = Node()
                node.column = col
                node.row_name = set_name
                # vertical link
                node.down = col
                node.up = col.up
                col.up.down = node
                col.up = node
                col.size += 1
                # horizontal link within the row
                if first is None:
                    first = node
                else:
                    node.right = first
                    node.left = first.left
                    first.left.right = node
                    first.left = node
    return header

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

solutions: List[List[str]] = []

def search(k: int, header: ColumnNode, solution: List[Node]):
    if header.right == header:
        solutions.append([node.row_name for node in solution])
        return
    # choose column with fewest rows
    c = header.right
    min_col = c
    min_size = c.size
    while c != header:
        if c.size < min_size:
            min_size = c.size
            min_col = c
        c = c.right
    cover(min_col)
    r = min_col.down
    while r != min_col:
        solution.append(r)
        j = r.right
        while j != r:
            cover(j.column)
            j = j.right
        search(k + 1, header, solution)
        solution.pop()
        j = r.left
        while j != r:
            uncover(j.column)
            j = j.left
        r = r.down
    uncover(min_col)

def main():
    header = build_links()
    search(0, header, [])
    # self‑contained verification test
    for sol in solutions:
        covered = set()
        counts = {}
        for name in sol:
            for e in sets[name]:
                covered.add(e)
                counts[e] = counts.get(e, 0) + 1
        assert covered == U, f"Solution does not cover U: {sol}"
        assert all(v == 1 for v in counts.values()), f"Element appears multiple times in {sol}"
    # emit witness
    import json, sys
    witness = {
        "polarity": "positive",
        "evidence": {"path": "execution://witness"},
        "data": {"solutions": solutions}
    }
    print("WITNESS:", json.dumps(witness))

if __name__ == "__main__":
    main()

```json
{
  "files": [
    {
      "filename": "exact_cover.py",
      "satisfies": [
        "R1",
        "R2",
        "R3"
      ],
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "#!/usr/bin/env python3"
      }
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "# Build exact‑cover matrix"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "def cover(col: ColumnNode):"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "# self‑contained verification test"
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
