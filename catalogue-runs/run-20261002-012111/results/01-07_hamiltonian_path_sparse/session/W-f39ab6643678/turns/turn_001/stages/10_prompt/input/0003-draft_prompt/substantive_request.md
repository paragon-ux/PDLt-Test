TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Determine whether the given undirected graph G with 12 nodes (labeled 0-11) and the specified edge list contains a Hamiltonian path (a path that visits every node exactly once). If a Hamiltonian path exists, output the complete path and include verification that the path visits all 12 nodes and that each consecutive pair of nodes in the path corresponds to a valid edge in the graph.
APPROACH/RISK NOTES:
Apply a backtracking search algorithm with pruning to explore candidate Hamiltonian paths, eliminating partial paths that cannot be extended to a full Hamiltonian path based on visited nodes and adjacency constraints.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- G
- 12 nodes
- 0-11
- Hamiltonian path
- verification
