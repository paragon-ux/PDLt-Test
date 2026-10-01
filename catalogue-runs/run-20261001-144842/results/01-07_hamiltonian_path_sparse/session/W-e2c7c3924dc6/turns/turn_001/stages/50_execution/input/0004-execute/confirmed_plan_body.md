PARSE the edge list to construct the undirected graph G
INITIATE a backtracking search with pruning to find a Hamiltonian path in G
FOR each recursive call
    EXTEND the current partial path by appending an adjacent node not already visited
    PRUNE the branch if the remaining unvisited nodes cannot be reached
ENDFOR
IF a complete path of 12 nodes is found THEN
    VERIFY that the path visits each of the 12 nodes exactly once
    VERIFY that each consecutive pair of nodes corresponds to an edge in G
    OUTPUT the Hamiltonian path
ENDIF
IF no complete path is found THEN
    OUTPUT that no Hamiltonian path exists
ENDIF
