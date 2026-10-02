READ NxM grid dimensions.
READ cell movement costs into a grid matrix, treating any cell with cost -1 as impassable.
INITIALIZE data structures for A* (open set, closed set, cost maps).
DEFINE heuristic function as Manhattan distance between a cell and the target cell.
WHILE open set is not empty DO
    SELECT cell with lowest f-score from open set.
    IF selected cell is the target THEN
        BREAK loop.
    ENDIF
    FOR each cardinal neighbour of selected cell DO
        IF neighbour is impassable THEN
            CONTINUE to next neighbour.
        ENDIF
        CALCULATE tentative g-score as current cell's g-score plus neighbour's movement cost.
        IF tentative g-score is lower than recorded g-score for neighbour THEN
            UPDATE neighbour's g-score and f-score.
            RECORD selected cell as neighbour's predecessor.
            ADD neighbour to open set if not already present.
        ENDIF
    ENDFOR
ENDWHILE
RECONSTRUCT path by tracing predecessors from target back to start, producing ordered list of (row, col) tuples.
CALCULATE total path cost as sum of movement costs of cells in the path.
WRITE Python implementation of the above A* procedure for weighted grid.
CREATE a 10x10 test grid with specified walls (cells with cost -1) and varying terrain costs.
EXECUTE the A* implementation on the test grid to obtain path and total cost.
EXECUTE Dijkstra's algorithm on the same test grid to obtain optimal path cost.
COMPARE A* total path cost to Dijkstra optimal cost to verify optimality.
RETURN the shortest path list and associated total cost.
