READ the undirected graph with nodes 0-11 and the provided edge list
DEFINE a function BACKTRACK(current_path, visited_set) that attempts to extend the path
IF length of current_path equals 12 THEN
VERIFY that every consecutive pair in current_path corresponds to an edge in the graph
OUTPUT the complete sequence as the Hamiltonian path
TERMINATE search
ENDIF
FOR each neighbor of the last node in current_path that is not in visited_set DO
IF adding the neighbor does not violate any edge constraint THEN
CALL BACKTRACK(current_path + [neighbor], visited_set ∪ {neighbor})
ENDIF
ENDFOR
END FUNCTION
INITIALIZE search by iterating over each node as a starting point:
CALL BACKTRACK([start_node], {start_node})
IF no path is found after all start nodes are exhausted THEN
REPORT that no Hamiltonian path exists for the given graph
ENDIF
