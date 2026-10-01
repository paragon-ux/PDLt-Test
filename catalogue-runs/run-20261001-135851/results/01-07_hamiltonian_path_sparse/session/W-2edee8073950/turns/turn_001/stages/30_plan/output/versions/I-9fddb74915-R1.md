PARSE the list of nodes and edges defining the undirected graph
INITIALIZE a backtracking search routine to build a Hamiltonian path
FOR each node as a potential start node DO
    CALL the backtracking routine with the start node and an empty visited set
    RECURSIVELY extend the current path by choosing an adjacent unvisited node
    PRUNE the search branch if no adjacent unvisited nodes remain before covering all nodes
    IF the path length reaches 12 THEN
        VERIFY that every consecutive pair in the path corresponds to an edge in the graph
        EMIT the complete sequence of node identifiers as the Hamiltonian path
        TERMINATE further search
    ENDIF
ENDFOR
