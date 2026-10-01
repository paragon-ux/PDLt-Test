IMPLEMENT A* pathfinding in Python for a grid defined as an NxM matrix where each cell has a non-negative movement cost, and a cost of -1 indicates an impassable cell.
ENSURE movement is 4-directional (up, down, left, right) and that moving into a cell incurs that cell's cost.
USE Manhattan distance as the heuristic.
RETURN the shortest path as a list of (row, col) coordinates and also RETURN the total cost.
TEST the implementation on a 10x10 grid containing walls and varying terrain costs.
COMPARE the A* path cost with Dijkstra on the same grid to VERIFY optimality.
