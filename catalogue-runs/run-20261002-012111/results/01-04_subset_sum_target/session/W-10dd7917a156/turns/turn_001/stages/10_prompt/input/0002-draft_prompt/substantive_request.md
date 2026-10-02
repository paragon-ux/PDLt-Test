TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Find and output all subsets of the given set S that sum exactly to the target value T = 40. For each solution, emit the subset and verify its sum. After enumerating all solutions, report the total number of solutions.
APPROACH/RISK NOTES:
Use a backtracking algorithm that explores the full search tree, systematically including or excluding each element of S and backtracking when the partial sum exceeds the target.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- T = 40
