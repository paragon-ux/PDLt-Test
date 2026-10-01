READ the undirected graph with nodes 0-11 and the given edge list
BACKTRACK search for a Hamiltonian path that visits each node exactly once, applying pruning to discard partial paths that cannot be extended to a full Hamiltonian path
VERIFY that the discovered path includes all 12 nodes
VERIFY that every consecutive node pair in the path corresponds to an edge in the graph
OUTPUT the complete sequence of node labels representing the Hamiltonian path if one exists
