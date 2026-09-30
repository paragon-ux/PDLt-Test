# exact_cover.py
# Implementation of Algorithm X with dancing links to find all exact covers for the given problem.

class DLXNode:
    __slots__ = ('left', 'right', 'up', 'down', 'column', 'row_id')
    def __init__(self):
        self.left = self.right = self.up = self.down = self
        self.column = None
        self.row_id = None

class ColumnNode(DLXNode):
    __slots__ = ('size', 'name')
    def __init__(self, name):
        super().__init__()
        self.size = 0
        self.name = name
        self.column = self

class DLX:
    def __init__(self, columns):
        self.header = ColumnNode('header')
        self.columns = {}
        last = self.header
        for name in columns:
            col = ColumnNode(name)
            self.columns[name] = col
            # link into header list
            last.right = col
            col.left = last
            last = col
        last.right = self.header
        self.header.left = last
        self.solution = []
        self.solutions = []

    def add_row(self, row_id, cols):
        first = None
        for col_name in cols:
            col = self.columns[col_name]
            node = DLXNode()
            node.column = col
            node.row_id = row_id
            # vertical links
            node.down = col
            node.up = col.up
            col.up.down = node
            col.up = node
            col.size += 1
            # horizontal links
            if first is None:
                first = node
                node.right = node.left = node
            else:
                node.right = first
                node.left = first.left
                first.left.right = node
                first.left = node
        # close the circular list if only one node
        if first.right is None:
            first.right = first.left = first

    def cover(self, col):
        col.right.left = col.left
        col.left.right = col.right
        i = col.down
        while i is not col:
            j = i.right
            while j is not i:
                j.down.up = j.up
                j.up.down = j.down
                j.column.size -= 1
                j = j.right
            i = i.down

    def uncover(self, col):
        i = col.up
        while i is not col:
            j = i.left
            while j is not i:
                j.column.size += 1
                j.down.up = j
                j.up.down = j
                j = j.left
            i = i.up
        col.right.left = col
        col.left.right = col

    def search(self, k=0):
        if self.header.right is self.header:
            self.solutions.append([node.row_id for node in self.solution])
            return
        # choose column with smallest size
        c = None
        s = float('inf')
        j = self.header.right
        while j is not self.header:
            if j.size < s:
                s = j.size
                c = j
                if s == 0:
                    break
            j = j.right
        if c is None or c.size == 0:
            return
        self.cover(c)
        r = c.down
        while r is not c:
            self.solution.append(r)
            j = r.right
            while j is not r:
                self.cover(j.column)
                j = j.right
            self.search(k+1)
            # backtrack
            self.solution.pop()
            j = r.left
            while j is not r:
                self.uncover(j.column)
                j = j.left
            r = r.down
        self.uncover(c)

# Problem definition
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

# Build DLX structure
column_names = [str(i) for i in sorted(U)]
dl = DLX(column_names)
for name, elems in sets.items():
    dl.add_row(name, [str(e) for e in elems])

dl.search()

# Self‑contained test
def test_solutions():
    assert dl.solutions, "No exact covers found"
    for sol in dl.solutions:
        covered = set()
        for set_name in sol:
            covered.update(sets[set_name])
        assert covered == U, f"Solution {sol} does not cover U"
        # check no element appears twice
        counts = {}
        for set_name in sol:
            for e in sets[set_name]:
                counts[e] = counts.get(e, 0) + 1
        assert all(c == 1 for c in counts.values()), f"Element duplication in solution {sol}"
    print('All tests passed')

if __name__ == "__main__":
    test_solutions()
    # Emit witness for the host
    import json, sys
    witness = {"solutions": dl.solutions}
    print('WITNESS: ' + json.dumps(witness))

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
        "section": "",
        "observed": "# exact_cover.py\\n# Implementation of Algorithm X with dancing links to find all exact covers for the given problem."
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
        "observed": "# exact_cover.py\\n# Implementation of Algorithm X with dancing links to find all exact covers for the given problem."
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "class DLXNode:"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "def test_solutions():"
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
