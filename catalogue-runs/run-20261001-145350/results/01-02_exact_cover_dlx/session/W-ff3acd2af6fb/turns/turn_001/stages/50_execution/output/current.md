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

# Build the exact cover matrix as a dict: element -> list of set names containing it
element_to_sets: Dict[int, List[str]] = {e: [] for e in U}
for name, elems in sets.items():
    for e in elems:
        element_to_sets[e].append(name)

# Dancing Links structures
class ColumnNode:
    def __init__(self, name):
        self.name = name
        self.size = 0
        self.up = self.down = self
        self.left = self.right = self
        self.column = self

class DataNode:
    def __init__(self, column: ColumnNode, row_name: str):
        self.column = column
        self.row_name = row_name
        self.up = self.down = self
        self.left = self.right = self

# Build the DLX header and column objects
header = ColumnNode('header')
column_lookup: Dict[str, ColumnNode] = {}
prev = header
for elem in sorted(U):
    col = ColumnNode(elem)
    column_lookup[elem] = col
    # link horizontally
    col.left = prev
    col.right = header
    prev.right = col
    header.left = col
    prev = col

# Insert data nodes
row_nodes: Dict[str, List[DataNode]] = {}
for set_name, elems in sets.items():
    first_node = None
    for e in elems:
        col = column_lookup[e]
        node = DataNode(col, set_name)
        # vertical linking
        node.down = col
        node.up = col.up
        col.up.down = node
        col.up = node
        col.size += 1
        # horizontal linking for the row
        if first_node is None:
            first_node = node
        else:
            node.left = first_node.left
            node.right = first_node
            first_node.left.right = node
            first_node.left = node
    row_nodes[set_name] = [node for node in (first_node, )]  # store at least one reference

solutions: List[List[str]] = []

def cover(col: ColumnNode):
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

def search(partial: List[str]):
    if header.right == header:
        solutions.append(partial.copy())
        return
    # choose column with smallest size (heuristic)
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
        partial.append(r.row_name)
        j = r.right
        while j != r:
            cover(j.column)
            j = j.right
        search(partial)
        # backtrack
        j = r.left
        while j != r:
            uncover(j.column)
            j = j.left
        partial.pop()
        r = r.down
    uncover(col)

# Run the algorithm
search([])

# Self‑contained test
def validate_solution(sol: List[str]) -> bool:
    covered: Set[int] = set()
    for name in sol:
        covered.update(sets[name])
    return covered == U and all(len(sets[name] & covered) == len(sets[name]) for name in sol)

assert all(validate_solution(sol) for sol in solutions), "Validation failed"

# Print witness
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
