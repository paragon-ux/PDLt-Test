READ the undirected graph definition with 12 nodes and the specified edge list
INITIALIZE an empty path sequence
PERFORM a backtracking search with pruning to construct a Hamiltonian path:
    SELECT a starting node
    RECURSIVELY extend the path by adding adjacent unvisited nodes
    PRUNE branches that cannot lead to a full Hamiltonian path
IF a Hamiltonian path is found THEN
    OUTPUT the complete sequence of node labels representing the path
    VERIFY that the path visits all 12 nodes
    VERIFY that each consecutive pair in the path corresponds to a valid edge from the provided edge list
ENDIF
