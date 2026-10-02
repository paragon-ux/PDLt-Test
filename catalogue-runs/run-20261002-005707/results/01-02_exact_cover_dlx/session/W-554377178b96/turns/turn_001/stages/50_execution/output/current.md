#!/usr/bin/env python3
"""Exact cover solver using Knuth's Algorithm X with dancing links.
Finds all exact covers of the universe U = {1,2,3,4,5,6,7,8,9} using the
subsets S1..S9 as defined in the task description.
A self‑contained test at the end verifies that each solution covers U exactly once.
"""

from typing import List, Dict, Optional

# ---------- Data structures ----------
class Node:
    __slots__ = ('left', 'right', 'up', 'down', 'column', 'row_id')
    def __init__(self, column: 'ColumnNode' = None, row_id: int = -1):
        self.left: 'Node' = self
        self.right: 'Node' = self
        self.up: 'Node' = self
        self.down: 'Node' = self
        self.column: ColumnNode = column
        self.row_id: int = row_id  # identifier of the row (subset index)

class ColumnNode(Node):
    __slots__ = ('size', 'name')
    def __init__(self, name: str):
        super().__init__(self, -1)
        self.size: int = 0          # number of 1s in the column
        self.name: str = name       # for debugging / output

# ---------- Dancing Links matrix construction ----------

def build_matrix(subsets: List[set], universe: set) -> ColumnNode:
    """Build the DLX structure.
    Returns the header node (a special column linking all columns).
    """
    # Header node that links all column headers
    header = ColumnNode('header')
    column_by_elem: Dict[int, ColumnNode] = {}
    # Create column header for each element of the universe
    for elem in sorted(universe):
        col = ColumnNode(str(elem))
        column_by_elem[elem] = col
        # link into header's list (to the left of header)
        col.right = header
        col.left = header.left
        header.left.right = col
        header.left = col
    # Build rows for each subset
    for row_index, subset in enumerate(subsets):
        first_node: Optional[Node] = None
        for elem in subset:
            col = column_by_elem[elem]
            node = Node(col, row_index)
            # vertical link (insert above column header)
            node.down = col
            node.up = col.up
            col.up.down = node
            col.up = node
            col.size += 1
            # horizontal link within the row
            if first_node is None:
                first_node = node
                node.right = node
                node.left = node
            else:
                node.right = first_node
                node.left = first_node.left
                first_node.left.right = node
                first_node.left = node
    # close header list
    header.right = header
    header.left = header
    return header

# ---------- Core DLX operations ----------

def cover(col: ColumnNode):
    """Remove column col and all rows that contain a node in that column."""
    # unlink column header
    col.right.left = col.left
    col.left.right = col.right
    # for each row in column
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
    """Restore column col and all rows that were removed by cover."""
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

# ---------- Algorithm X recursive search ----------

def search(solution: List[int], header: ColumnNode, solutions: List[List[int]]):
    # If no columns remain, we have a complete cover
    if header.right == header:
        solutions.append(solution.copy())
        return
    # Choose column with minimal size (heuristic)
    # (Knuth's recommendation for efficiency)
    c = header.right
    min_size = c.size
    col = c
    while c != header:
        if c.size < min_size:
            min_size = c.size
            col = c
            if min_size == 0:
                break
        c = c.right
    if min_size == 0:
        return  # dead end
    cover(col)
    r = col.down
    while r != col:
        solution.append(r.row_id)
        j = r.right
        while j != r:
            cover(j.column)
            j = j.right
        search(solution, header, solutions)
        # backtrack
        solution.pop()
        j = r.left
        while j != r:
            uncover(j.column)
            j = j.left
        r = r.down
    uncover(col)

# ---------- Helper to translate solution indices to subset names ----------

def translate_solution(sol: List[int], subsets_names: List[str]) -> List[str]:
    return [subsets_names[i] for i in sol]

# ---------- Self‑contained test harness ----------

def run_test():
    universe = {1,2,3,4,5,6,7,8,9}
    subsets = [
        {1,2,3},   # S1
        {4,5,6},   # S2
        {7,8,9},   # S3
        {1,4,7},   # S4
        {2,5,8},   # S5
        {3,6,9},   # S6
        {1,5,9},   # S7
        {2,6,7},   # S8
        {3,4,8},   # S9
    ]
    subsets_names = [f'S{i+1}' for i in range(len(subsets))]
    header = build_matrix(subsets, universe)
    solutions: List[List[int]] = []
    search([], header, solutions)
    # Verify each solution covers universe exactly once
    for sol in solutions:
        covered = set()
        for row_idx in sol:
            covered ^= subsets[row_idx]  # XOR works because rows are disjoint in exact cover
        assert covered == universe, f"Solution does not cover universe: {sol}"
    # Print solutions in a readable format
    print(f"Found {len(solutions)} exact cover solution(s):")
    for idx, sol in enumerate(solutions, 1):
        names = translate_solution(sol, subsets_names)
        print(f"Solution {idx}: {{ {', '.join(names)} }}")

if __name__ == "__main__":
    run_test()
