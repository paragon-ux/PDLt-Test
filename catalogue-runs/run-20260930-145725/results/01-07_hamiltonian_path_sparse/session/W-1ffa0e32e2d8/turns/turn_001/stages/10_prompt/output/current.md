DETERMINE whether the undirected graph G with 12 nodes labeled 0-11 and the provided edge list contains a Hamiltonian path.
IF a Hamiltonian path exists, OUTPUT the complete sequence of node labels representing the path.
USE a backtracking search with pruning to explore candidate paths.
VERIFY that the resulting path visits all 12 nodes exactly once and that each consecutive pair of nodes in the path corresponds to a valid edge in the edge list.
