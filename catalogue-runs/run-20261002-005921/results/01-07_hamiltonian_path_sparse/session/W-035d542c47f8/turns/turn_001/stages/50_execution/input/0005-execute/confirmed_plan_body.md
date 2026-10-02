PARSE the node and edge definitions from the prompt
BUILD an adjacency list for graph G
DEFINE a recursive FUNCTION SEARCH(current_path, visited_set)
    IF length of current_path = 12 THEN
        VERIFY that each consecutive pair in current_path is an edge in G
        EMIT the complete Hamiltonian path
        TERMINATE the search
    ENDIF
    IF no neighbor of the last node in current_path is unvisited THEN
        BACKTRACK (return)
    ENDIF
    FOR each neighbor of the last node in current_path DO
        IF neighbor NOT IN visited_set THEN
            ADD neighbor to current_path and visited_set
            CALL SEARCH with updated parameters
            REMOVE neighbor from current_path and visited_set (backtrack)
        ENDIF
    ENDFOR
END FUNCTION
FOR each node in G as start_node DO
    INITIALIZE current_path with start_node and visited_set containing start_node
    CALL SEARCH
    IF SEARCH produced a Hamiltonian path THEN
        STOP further start_node iterations
    ENDIF
ENDFOR
IF no Hamiltonian path has been emitted THEN
    EMIT a statement that no Hamiltonian path exists in G
ENDIF
