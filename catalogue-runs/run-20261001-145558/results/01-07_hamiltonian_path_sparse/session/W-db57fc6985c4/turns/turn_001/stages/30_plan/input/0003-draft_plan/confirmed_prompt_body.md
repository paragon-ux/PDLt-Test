READ the undirected graph G with nodes 0-11 and the supplied edge list
DETERMINE whether G contains a Hamiltonian path that visits every node exactly once
IF a Hamiltonian path exists THEN OUTPUT the complete sequence of node labels in order
USE a backtracking search with pruning to explore candidate paths
VERIFY that the path includes all 12 nodes and that each consecutive pair of nodes corresponds to a valid edge from the list
