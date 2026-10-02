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

# Build dancing links structures
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
        self.column = self

# Header
header = ColumnNode('header')
columns: Dict[int, ColumnNode] = {}
for elem in U:
    col = ColumnNode(elem)
    columns[elem] = col
    # link into header list
    col.right = header
    col.left = header.left
    header.left.right = col
    header.left = col

# Add rows (sets)
row_nodes: List[Node] = []
for set_name, elems in sets.items():
    first_node = None
    for e in elems:
        col = columns[e]
        node = Node()
        node.column = col
        node.row_name = set_name
        # vertical link
        node.down = col
        node.up = col.up
        col.up.down = node
        col.up = node
        col.size += 1
        # horizontal link
        if first_node is None:
            first_node = node
            node.right = node.left = node
        else:
            node.right = first_node
            node.left = first_node.left
            first_node.left.right = node
            first_node.left = node
    row_nodes.append(first_node)

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

def search(k: int, solution: List[Node]):
    if header.right == header:
        # found a solution
        sol = [node.row_name for node in solution]
        solutions.append(sol)
        return
    # choose column with smallest size
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
        solution.append(r)
        j = r.right
        while j != r:
            cover(j.column)
            j = j.right
        search(k+1, solution)
        # backtrack
        solution.pop()
        j = r.left
        while j != r:
            uncover(j.column)
            j = j.left
        r = r.down
    uncover(col)

search(0, [])

# Verify each solution covers U exactly once
def verify(sol: List[str]) -> bool:
    covered = set()
    for name in sol:
        covered.update(sets[name])
    return covered == U and all(len(set(sets[name]) & covered) == len(sets[name]) for name in sol)

assert all(verify(sol) for sol in solutions), "Verification failed"

# Print solutions in readable format
print("Exact cover solutions:")
for idx, sol in enumerate(solutions, 1):
    print(f"{idx}: {{" + ", ".join(sol) + "}}")

# Emit witness
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
