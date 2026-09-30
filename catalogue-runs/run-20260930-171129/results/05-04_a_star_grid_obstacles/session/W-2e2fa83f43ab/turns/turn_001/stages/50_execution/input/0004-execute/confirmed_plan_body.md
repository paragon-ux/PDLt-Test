VALIDATE the supplied grid matrix dimensions and cell cost values
INITIALIZE open set data structure for A* search
DEFINE Manhattan distance function as heuristic
DEFINE function to retrieve walkable 4-directional neighbors, excluding cells with cost -1
WHILE open set is not empty
SELECT node with lowest f-score (g + heuristic) from open set
IF selected node is the goal cell
RECONSTRUCT path by backtracking predecessor links
CALCULATE total path cost as sum of entered cell costs
RETURN ordered list of (row, col) coordinates and total cost
ENDIF
FOR each neighbor of selected node
COMPUTE tentative g-score as current g-score plus neighbor cell cost
IF neighbor not in open set OR tentative g-score is lower than recorded g-score
RECORD neighbor predecessor as current node
UPDATE neighbor g-score and f-score
ADD neighbor to open set if not present
ENDIF
ENDFOR
ENDWHILE
IF goal not reached
RETURN indication of no viable path
ENDIF
EXECUTE a Dijkstra algorithm on the same grid to obtain optimal path cost for verification
COMPARE A* returned total cost with Dijkstra optimal cost for consistency
DEFINE a 10x10 test grid containing impassable cells (-1) and varied terrain costs
RUN the A* implementation on the test grid
OUTPUT the resulting path list and total cost along with verification result
