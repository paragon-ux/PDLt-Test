DEFINE a Python function implementing A* pathfinding on an NxM weighted grid
ENSURE each grid cell has a non-negative movement cost; treat cells with cost -1 as impassable
ALLOW movement only in 4-directional steps (up, down, left, right)
FOR each move INTO a cell, ADD the cost of that cell to the accumulated path cost
USE Manhattan distance as the heuristic for A*
RETURN the shortest path as a list of (row, col) coordinates and the total path cost
CREATE a 10x10 grid that includes walls and varying terrain costs
SELECT start and goal coordinates within the grid
EXECUTE the A* function on the grid to obtain a path and its total cost
IMPLEMENT Dijkstra's algorithm on the same grid to compute the optimal path cost
COMPARE the A* path cost with the optimal cost from Dijkstra to verify correctness
INCLUDE the following operative task entities verbatim: A*, Python, NxM, -1, 4-directional, Manhattan distance, (row, col), 10x10, Dijkstra
