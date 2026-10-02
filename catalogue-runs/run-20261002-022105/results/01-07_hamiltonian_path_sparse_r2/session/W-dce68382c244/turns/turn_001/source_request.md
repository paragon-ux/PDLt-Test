Given an undirected graph G with 12 nodes (labeled 0-11) and the following edge list:
Edges: [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11), (0,3), (2,7), (4,9), (6,11), (1,8)]

Determine whether G contains a Hamiltonian path (a path that visits every node exactly once). If one exists, output the complete path. Use a backtracking search with pruning. Include verification that the path visits all 12 nodes and every consecutive pair in the path is a valid edge.
