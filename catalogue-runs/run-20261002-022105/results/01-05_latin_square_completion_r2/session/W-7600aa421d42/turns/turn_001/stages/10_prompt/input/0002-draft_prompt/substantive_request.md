TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
The user requests to fill the empty cells (marked 0) of a partially filled 7x7 Latin square so that each row and each column contains the numbers 1 through 7 exactly once. The solution must be generated using a constraint-propagation algorithm with backtracking, and the completed grid must be emitted along with verification that each row and column is a permutation of {1,...,7}.
APPROACH/RISK NOTES:
Use a constraint-propagation solver with backtracking to assign values to the empty cells, reducing domains and exploring possibilities until a valid Latin square is found.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- 7x7 Latin square
- backtracking
- permutation of {1,...,7}
