TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Given an undirected graph G with 12 nodes labeled 0-11 and edges [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11), (0,3), (2,7), (4,9), (6,11), (1,8)], determine whether G contains a Hamiltonian path (a path that visits every node exactly once). If a Hamiltonian path exists, output the complete path and verify that the path visits all 12 nodes and each consecutive pair in the path is a valid edge.
APPROACH/RISK NOTES:
Use a backtracking search with pruning.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- G
