READ the undirected graph G with 12 nodes labeled 0-11 and edge list [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11), (0,3), (2,7), (4,9), (6,11), (1,8)]
INITIALIZE an empty collection PATHS_FOUND
DEFINE BACKTRACK(current_path, visited_set):
    IF LENGTH(current_path) == 12 THEN
        ADD current_path TO PATHS_FOUND
        RETURN
    ENDIF
    FOR EACH neighbor OF the last node IN current_path:
        IF neighbor NOT IN visited_set AND edge (last node, neighbor) EXISTS IN the edge list THEN
            APPEND neighbor TO current_path
            ADD neighbor TO visited_set
            BACKTRACK(current_path, visited_set)
            REMOVE neighbor FROM current_path
            REMOVE neighbor FROM visited_set
        ENDIF
    ENDFOR
FOR EACH start_node IN [0-11]:
    SET current_path TO [start_node]
    SET visited_set TO {start_node}
    BACKTRACK(current_path, visited_set)
ENDFOR
IF PATHS_FOUND IS NOT EMPTY THEN
    SELECT a Hamiltonian path FROM PATHS_FOUND
    VERIFY that the selected path visits all 12 nodes
    VERIFY that each consecutive pair in the path corresponds to an edge in the edge list
    OUTPUT the verified Hamiltonian path
ENDIF
