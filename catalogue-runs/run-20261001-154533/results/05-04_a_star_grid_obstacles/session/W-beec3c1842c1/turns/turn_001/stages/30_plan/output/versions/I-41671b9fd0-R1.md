DESIGN a Python function named a_star_pathfinding with parameters grid, start, goal
ENSURE the function treats cells with cost -1 as impassable
IMPLEMENT movement in 4-directional steps only (up, down, left, right)
CALCULATE step cost by adding the cost of the destination cell to the accumulated path cost
USE Manhattan distance as the heuristic for A*
RETURN the shortest path as a list of (row, col) coordinates and the total path cost
CONSTRUCT a 10x10 NxM weighted grid containing non-negative movement costs and -1 cells as walls
POPULATE the grid with varying terrain costs
SELECT start and goal coordinates within the 10x10 grid that are traversable
EXECUTE the A* function on the grid to obtain a path and its total cost
DESIGN a Python function implementing Dijkstra's algorithm on the same grid
EXECUTE Dijkstra's algorithm on the grid with the same start and goal to compute the optimal path cost
COMPARE the A* path cost with the optimal cost from Dijkstra to verify correctness
REPORT the verification outcome
