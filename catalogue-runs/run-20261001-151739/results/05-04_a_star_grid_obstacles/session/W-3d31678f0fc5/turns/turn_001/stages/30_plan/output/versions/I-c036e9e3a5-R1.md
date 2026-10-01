PARSE the input grid dimensions and movement costs
VALIDATE that each cell has a non-negative cost or -1 for impassable
DEFINE a Manhattan distance heuristic function for two cells
INITIALIZE an empty priority queue (open set) and insert the start cell with its f‑score
INITIALIZE a cost map with the start cell cost set to zero
INITIALIZE a predecessor map for path reconstruction
WHILE the priority queue is not empty
    POP the cell with the lowest f‑score
    IF the popped cell is the goal
        RECONSTRUCT the path by backtracking through the predecessor map
        RETURN the path and its total cost
    ENDIF
    FOR each of the four orthogonal neighbors of the current cell
        IF the neighbor cell is impassable (-1)
            CONTINUE to the next neighbor
        ENDIF
        CALCULATE tentative_g as current cell g‑score plus neighbor cell movement cost
        IF tentative_g is lower than the recorded cost for the neighbor
            UPDATE the neighbor's cost in the cost map to tentative_g
            SET the neighbor's predecessor to the current cell
            COMPUTE f‑score as tentative_g plus the Manhattan distance heuristic to the goal
            ADD or update the neighbor in the priority queue with its f‑score
        ENDIF
    ENDFOR
ENDWHILE
IF no path was found
    RETURN an empty path and indicate failure
ENDIF
TEST the implementation on a 10x10 grid containing walls (impassable cells) and varying terrain costs
COMPARE the total cost of the A* path with the total cost obtained by Dijkstra's algorithm on the same grid to verify optimality
