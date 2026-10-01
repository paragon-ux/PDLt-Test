TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement A* pathfinding on a weighted grid in Python. The grid is an NxM matrix where each cell has a non-negative movement cost; a cost of -1 indicates impassable cells. Movement is limited to 4-directional (up, down, left, right) steps, and moving into a cell incurs the cost of that cell. Use Manhattan distance as the heuristic, which is admissible for 4-directional movement with uniform minimum cost. The function should return the shortest path as a list of (row, col) coordinates and the total path cost. Additionally, test the implementation on a 10x10 grid that includes walls and varying terrain costs, and verify that the computed path cost matches the optimal cost by comparing the result with Dijkstra's algorithm on the same grid.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- A*
- Python
- NxM
- -1
- 4-directional
- Manhattan distance
- (row, col)
- 10x10
- Dijkstra
