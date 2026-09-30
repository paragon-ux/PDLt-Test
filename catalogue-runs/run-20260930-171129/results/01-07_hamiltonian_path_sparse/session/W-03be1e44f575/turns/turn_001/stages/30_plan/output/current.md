READ the undirected graph with nodes 0-11 and the provided edge list
DEFINE a BACKTRACK procedure that takes CURRENT_PATH and VISITED_SET
IF the length of CURRENT_PATH equals 12 THEN
VERIFY that each consecutive pair in CURRENT_PATH corresponds to an edge in the graph
EMIT CURRENT_PATH as the Hamiltonian path
TERMINATE the search
ENDIF
FOR each NEIGHBOR of the last node in CURRENT_PATH that is not in VISITED_SET DO
IF adding NEIGHBOR does not violate any edge constraint THEN
CALL BACKTRACK with CURRENT_PATH extended by NEIGHBOR and VISITED_SET union {NEIGHBOR}
ENDIF
ENDFOR
END PROCEDURE
FOR each START_NODE in the set of nodes 0‑11 DO
CALL BACKTRACK with INITIAL_PATH [START_NODE] and VISITED_SET {START_NODE}
ENDFOR
IF no Hamiltonian path has been emitted after all start nodes are exhausted THEN
REPORT that no Hamiltonian path exists for the given graph
ENDIF
