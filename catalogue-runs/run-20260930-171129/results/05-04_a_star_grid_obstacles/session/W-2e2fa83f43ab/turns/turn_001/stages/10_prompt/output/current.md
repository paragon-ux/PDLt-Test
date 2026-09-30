IMPLEMENT A* pathfinding on a weighted grid in Python.
USE a grid represented as an NxM matrix where each cell contains a non-negative movement cost, with -1 indicating an impassable cell.
ALLOW 4-directional movement (up, down, left, right); moving into a cell incurs that cell's cost.
APPLY Manhattan distance as the heuristic function.
RETURN the shortest path as an ordered list of (row, col) coordinates together with the total path cost.
INCLUDE a test case using a 10x10 grid that contains walls and varying terrain costs.
VERIFY that the path cost returned by the A* implementation matches the optimal path cost produced by Dijkstra's algorithm on the same grid.
