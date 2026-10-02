PARSE the supplied graph specification to extract the node count and edge list.
BUILD an adjacency structure for the undirected graph.
INITIALIZE a visited set and a path list.
DEFINE a RECURSIVE BACKTRACK procedure that attempts to extend the current path by selecting adjacent unvisited nodes.
PRUNE the search when a node has no unvisited neighbors or when remaining unvisited nodes cannot be reached.
FOR each node in the graph as a potential start node, CALL the BACKTRACK procedure.
IF a complete path covering all 12 nodes is discovered, STORE the path.
VERIFY that the stored path includes all 12 nodes and that each consecutive pair corresponds to an edge in the adjacency structure.
EMIT the verified Hamiltonian path; otherwise, EMIT that no Hamiltonian path exists.
