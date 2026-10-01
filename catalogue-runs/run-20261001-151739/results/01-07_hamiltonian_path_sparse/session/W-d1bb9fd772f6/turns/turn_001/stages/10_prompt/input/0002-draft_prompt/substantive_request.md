TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Determine whether the undirected graph G with 12 nodes labeled 0 through 11 and the provided edge list contains a Hamiltonian path. If a Hamiltonian path exists, output the complete path. Verify that the path includes all 12 nodes and that each consecutive pair of nodes in the path corresponds to an edge in the graph.
APPROACH/RISK NOTES:
Use a backtracking search with pruning to explore possible node orderings, stopping when a Hamiltonian path is found or all possibilities are exhausted. Include verification steps that confirm the path visits every node exactly once and that every adjacent node pair is a valid edge.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- G
- 12
