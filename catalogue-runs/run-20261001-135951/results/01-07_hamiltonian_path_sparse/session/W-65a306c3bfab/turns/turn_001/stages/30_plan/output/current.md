READ the undirected graph edge list
BUILD adjacency representation of the 12-node graph
INITIATE backtracking search to construct a Hamiltonian path
PRUNE search branches when a node cannot be visited without violating Hamiltonian constraints
WHEN a complete path of length 12 is constructed
OUTPUT the node sequence representing the Hamiltonian path
VERIFY that the path includes all 12 distinct nodes
VERIFY that each consecutive node pair in the sequence corresponds to an edge in the graph
