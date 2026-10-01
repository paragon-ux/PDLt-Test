import json
from typing import List, Dict, Set

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

# Build the exact cover matrix (dictionary of element -> sets containing it)
element_to_sets: Dict[int, Set[str]] = {e: set() for e in U}
for name, elems in sets.items():
    for e in elems:
        element_to_sets[e].add(name)

# Dancing Links structures (simplified for this small problem)
class DLXNode:
    def __init__(self):
        self.left = self.right = self.up = self.down = self
        self.column = None
        self.row_name = None

class ColumnNode(DLXNode):
    def __init__(self, name):
        super().__init__()
        self.size = 0
        self.name = name
        self.column = self

# Build header list
header = ColumnNode('header')
column_nodes: Dict[int, ColumnNode] = {}
prev = header
for e in sorted(U):
    col = ColumnNode(e)
    column_nodes[e] = col
    # link horizontally
    prev.right = col
    col.left = prev
    prev = col
# close loop
prev.right = header
header.left = prev

# Add rows (sets) to the structure
row_nodes: Dict[str, List[DLXNode]] = {}
for set_name, elems in sets.items():
    first_node = None
    for e in elems:
        col = column_nodes[e]
        node = DLXNode()
        node.column = col
        node.row_name = set_name
        # vertical linkage
        node.down = col
        node.up = col.up
        col.up.down = node
        col.up = node
        col.size += 1
        # horizontal linkage within the row
        if first_node is None:
            first_node = node
            node.right = node.left = node
        else:
            node.right = first_node
            node.left = first_node.left
            first_node.left.right = node
            first_node.left = node
    row_nodes[set_name] = [first_node]

solutions: List[List[str]] = []
search_path: List[DLXNode] = []

def cover(col: ColumnNode):
    # Remove column header
    col.right.left = col.left
    col.left.right = col.right
    # Remove rows
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
        # all columns covered
        solution = [node.row_name for node in search_path]
        solutions.append(solution)
        return
    # Choose column with smallest size (heuristic)
    c = header.right
    min_size = c.size
    col = c
    while c != header:
        if c.size < min_size:
            min_size = c.size
            col = c
        c = c.right
    cover(col)
    r = col.down
    while r != col:
        search_path.append(r)
        j = r.right
        while j != r:
            cover(j.column)
            j = j.right
        search(k+1)
        # backtrack
        r_back = search_path.pop()
        j = r_back.left
        while j != r_back:
            uncover(j.column)
            j = j.left
        r = r.down
    uncover(col)

# Run Algorithm X
search(0)

# Self‑contained test
def verify_solution(sol: List[str]):
    covered = set()
    for name in sol:
        covered.update(sets[name])
    return covered == U and all(len(set.intersection(sets[a], sets[b])) == 0 for a in sol for b in sol if a != b)

assert all(verify_solution(sol) for sol in solutions), "A solution failed verification"

# Output witness with the found solutions
witness = {
    "polarity": "positive",
    "data": {
        "solutions": solutions
    }
}
print("WITNESS: " + json.dumps(witness))

```json
{
  "files": [],
  "reconciliation": [],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
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
