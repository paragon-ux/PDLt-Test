LOAD the undirected graph G with its 12 nodes and edge list.
FOR each node in G as a potential start node DO
    INITIALIZE a path containing the start node.
    PERFORM a BACKTRACKING SEARCH with pruning to extend the path:
        WHILE the path length is less than 12 DO
            SELECT an adjacent node not yet visited.
            IF such a node exists THEN
                APPEND the node to the path.
            ELSE
                PRUNE the current partial path and backtrack.
            ENDIF
        ENDWHILE
    IF a complete path of length 12 is discovered THEN
        EMIT the Hamiltonian path.
        VERIFY that the path includes all 12 distinct nodes.
        VERIFY that each consecutive node pair corresponds to an edge in G.
        TERMINATE the search.
    ENDIF
ENDFOR
IF no Hamiltonian path was found after exploring all start nodes THEN
    REPORT that no Hamiltonian path exists.
ENDIF
