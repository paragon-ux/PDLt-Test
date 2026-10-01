READ the weighted grid definition and movement costs
DEFINE start and goal coordinates for the pathfinding task
INITIALIZE open set with the start node and CLOSED set as empty
CALCULATE Manhattan distance heuristic for each node
WHILE open set is not empty
    SELECT node with lowest f‑score (g‑score + heuristic) from open set
    IF selected node is the goal
        RECONSTRUCT path by tracing predecessor links
        BREAK loop
    MOVE selected node from open set to CLOSED set
    FOR each 4‑directional neighbor (up, down, left, right) of the selected node
        IF neighbor cell value is -1 (impassable) OR neighbor is in CLOSED set
            CONTINUE to next neighbor
        COMPUTE tentative g‑score as current node g‑score plus neighbor cell movement cost
        IF neighbor not in open set OR tentative g‑score is lower than previously recorded g‑score
            RECORD predecessor of neighbor as current node
            UPDATE neighbor g‑score to tentative g‑score
            UPDATE neighbor f‑score as g‑score plus Manhattan heuristic
            IF neighbor not in open set
                ADD neighbor to open set
ENDWHILE
OUTPUT the ordered list of (row, col) coordinates representing the shortest path
OUTPUT the total accumulated cost of the path
TEST the implementation on a 10 × 10 grid containing walls and varying terrain costs
COMPARE the resulting path and cost against the result of Dijkstra's algorithm on the same grid to verify optimality
