READ the grid dimensions as NxM.
READ the grid cell movement costs; TREAT any cell with cost -1 as impassable.
ALLOW movement from a cell to its four cardinal neighbours (up, down, left, right); MOVING INTO a neighbour incurs the neighbour's movement cost.
USE Manhattan distance as the heuristic for A*.
IMPLEMENT A* pathfinding algorithm in Python for the described weighted grid.
RETURN the shortest path as an ordered list of (row, col) coordinate tuples and the total path cost.
