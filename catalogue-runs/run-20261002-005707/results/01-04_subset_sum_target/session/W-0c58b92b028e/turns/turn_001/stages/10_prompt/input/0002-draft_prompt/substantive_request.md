TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Find all subsets of the set S = {3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21} that sum exactly to the target T = 40. For each solution, emit the subset and verify its sum, and finally report the total number of solutions.
APPROACH/RISK NOTES:
Use a backtracking algorithm that explores the full search tree to enumerate all possible subsets.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- S = {3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21}
- T = 40
