PARSE the supplied graph definition to obtain the set of nodes and the edge list.
BUILD an adjacency structure representing the undirected graph.
INITIALIZE a backtracking search using pruning heuristics.
FOR each node in the graph DO
    START a recursive search with the current node as the initial path element.
    WHILE extending the current partial path DO
        SELECT a neighbor of the last node that has not yet been visited.
        IF adding the neighbor violates any pruning rule THEN
            BACKTRACK.
        ELSE
            EXTEND the path with the neighbor.
        ENDIF
    ENDWHILE
    IF the path length equals the total number of nodes THEN
        RECORD the complete Hamiltonian path.
    ENDIF
ENDFOR
IF a Hamiltonian path has been recorded THEN
    OUTPUT the full path.
    VERIFY that the path contains all 12 nodes and that each consecutive pair of nodes is an edge in the graph.
ELSE
    OUTPUT a statement that no Hamiltonian path exists.
ENDIF
