import sys
from typing import List, Dict, Tuple

# --- Dancing Links implementation for Exact Cover (Algorithm X) ---

class Node:
    __slots__ = ('L', 'R', 'U', 'D', 'C', 'row')
    def __init__(self):
        self.L = self.R = self.U = self.D = self
        self.C = None  # type: ColumnNode
        self.row = None  # identifier of the row this node belongs to

class ColumnNode(Node):
    __slots__ = ('size', 'name')
    def __init__(self, name):
        super().__init__()
        self.size = 0
        self.name = name
        self.C = self

class DLX:
    def __init__(self, cols: List[int]):
        self.header = ColumnNode('header')
        self.columns: Dict[int, ColumnNode] = {}
        last = self.header
        for c in cols:
            col = ColumnNode(c)
            self.columns[c] = col
            # link column into header list
            last.R = col
            col.L = last
            last = col
        last.R = self.header
        self.header.L = last
        self.solution: List[ColumnNode] = []

    def add_row(self, row_id, cols: List[int]):
        first = None
        for c in cols:
            column = self.columns[c]
            node = Node()
            node.C = column
            node.row = row_id
            # vertical links
            node.U = column.U
            node.D = column
            column.U.D = node
            column.U = node
            column.size += 1
            # horizontal links
            if first is None:
                first = node
                node.R = node.L = node
            else:
                node.R = first
                node.L = first.L
                first.L.R = node
                first.L = node

    def cover(self, col: ColumnNode):
        col.R.L = col.L
        col.L.R = col.R
        i = col.D
        while i != col:
            j = i.R
            while j != i:
                j.D.U = j.U
                j.U.D = j.D
                j.C.size -= 1
                j = j.R
            i = i.D

    def uncover(self, col: ColumnNode):
        i = col.U
        while i != col:
            j = i.L
            while j != i:
                j.C.size += 1
                j.D.U = j
                j.U.D = j
                j = j.L
            i = i.U
        col.R.L = col
        col.L.R = col

    def search(self, k: int = 0):
        if self.header.R == self.header:
            yield list(self.solution)
            return
        # choose column with minimal size
        c = None
        s = sys.maxsize
        j = self.header.R
        while j != self.header:
            if j.size < s:
                s = j.size
                c = j
                if s == 0:
                    break
            j = j.R
        if c is None or c.size == 0:
            return
        self.cover(c)
        r = c.D
        while r != c:
            self.solution.append(r)
            j = r.R
            while j != r:
                self.cover(j.C)
                j = j.R
            yield from self.search(k+1)
            # backtrack
            self.solution.pop()
            j = r.L
            while j != r:
                self.uncover(j.C)
                j = j.L
            r = r.D
        self.uncover(c)

# --- Problem definition ---
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

# Build DLX matrix
cols = list(U)
dlx = DLX(cols)
for name, elems in sets.items():
    dlx.add_row(name, list(elems))

# Collect all exact covers
solutions: List[List[str]] = []
for sol_nodes in dlx.search():
    sol = [node.row for node in sol_nodes]
    solutions.append(sol)

# Self‑contained test
def verify_solution(sol: List[str]) -> bool:
    covered = set()
    for name in sol:
        elems = sets[name]
        if covered & elems:
            return False
        covered |= elems
    return covered == U

assert all(verify_solution(sol) for sol in solutions), "A solution failed verification"

# Output witness
import json
witness = {
    "polarity": "positive",
    "evidence": {"path": "execution://witness"},
    "data": {"solutions": solutions}
}
print('WITNESS: ' + json.dumps(witness))

```json
{
  "files": [
    {
      "filename": "exact_cover_dlx.py",
      "satisfies": [
        "R1",
        "R2"
      ],
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "# --- Dancing Links implementation for Exact Cover (Algorithm X) ---"
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
        "observed": "def search(self, k: int = 0):"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "assert all(verify_solution(sol) for sol in solutions), \\\"A solution failed verification\\\""
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
