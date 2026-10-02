TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Given an undirected graph G with 12 nodes labeled 0-11 and a specified edge list, determine whether G contains a Hamiltonian path that visits every node exactly once. If such a path exists, output the complete path and verify that it includes all 12 nodes and that each consecutive pair of nodes in the path corresponds to an edge in the graph.
APPROACH/RISK NOTES:
Use a backtracking search with pruning to explore possible paths.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- 12
- 0-11
- Hamiltonian path
