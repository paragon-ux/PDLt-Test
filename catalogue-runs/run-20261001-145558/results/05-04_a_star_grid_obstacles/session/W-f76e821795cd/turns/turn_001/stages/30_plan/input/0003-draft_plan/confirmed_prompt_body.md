READ the weighted grid definition and movement costs
DEFINE the start and goal coordinates for the pathfinding task
IMPLEMENT the A* algorithm using 4-directional movement (up, down, left, right)
USE the Manhattan distance as the heuristic function
SET the cost of moving into a cell equal to the cell's non‑negative movement cost
TREAT cells with a value of -1 as impassable obstacles
RETURN the shortest path as an ordered list of (row, col) coordinates
RETURN the total accumulated cost of the path
TEST the implementation on a 10 × 10 grid containing walls and varying terrain costs
VERIFY optimality by comparing the resulting path and cost against the result of Dijkstra's algorithm on the same grid
