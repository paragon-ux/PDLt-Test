READ the undirected graph G with nodes 0 through 11 and the given edges
INITIALIZE a backtracking search with pruning for a Hamiltonian path in G
FOR each node in G as a start node DO
    START a new path containing the start node
    RECURSIVELY EXTEND the path
        SELECT an adjacent node not yet visited
        APPEND the node to the path
        IF the path length equals 12 THEN
            STORE the complete path as a candidate solution
            BREAK the recursion
        ENDIF
        PRUNE the branch if no further extension is possible
    END RECURSIVE EXTENSION
END FOR
IF a candidate Hamiltonian path was found THEN
    EMIT the Hamiltonian path
    VERIFY that the path visits all 12 nodes
    VERIFY that each consecutive pair of nodes in the path corresponds to a valid edge in G
ELSE
    EMIT that no Hamiltonian path exists
ENDIF
