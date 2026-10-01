READ the undirected graph G with nodes 0-11 and the supplied edge list
INITIALIZE a backtracking search to construct a candidate path
FOR each node as a potential start node DO
    RECURSIVELY EXTEND the current path by adding an adjacent unvisited node
    PRUNE the search branch if no adjacent unvisited nodes remain while the path is incomplete
    CONTINUE until the path includes all 12 nodes
ENDFOR
IF a Hamiltonian path is found THEN
    VERIFY that every consecutive pair of nodes in the path corresponds to a valid edge from the list
    OUTPUT the complete sequence of node labels in order
ENDIF
