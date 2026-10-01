PARSE the edge list into an adjacency structure
INITIALIZE an empty path container
DEFINE BACKTRACK(current_node, visited_set, current_path)
    IF length of current_path equals 12 THEN
        EMIT the discovered Hamiltonian path
        TERMINATE the search
    ENDIF
    FOR each neighbor of current_node
        IF neighbor not in visited_set THEN
            ADD neighbor to visited_set and to current_path
            CALL BACKTRACK(neighbor, visited_set, current_path)
            REMOVE neighbor from visited_set and from current_path
        ENDIF
    ENDFOR
ENDDEFINE
FOR each start_node from 0 to 11
    CALL BACKTRACK(start_node, {start_node}, [start_node])
ENDFOR
VERIFY that the emitted path includes all 12 nodes and that every consecutive node pair corresponds to a valid edge
