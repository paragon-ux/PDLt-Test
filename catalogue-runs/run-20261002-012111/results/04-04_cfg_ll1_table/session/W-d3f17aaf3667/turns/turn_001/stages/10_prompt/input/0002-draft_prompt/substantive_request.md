TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Compute FIRST sets for all non-terminals (E, E', T, T', F) of the provided grammar (E → T E', E' → + T E' | ε, T → F T', T' → * F T' | ε, F → ( E ) | id). Compute FOLLOW sets for the same non-terminals. Construct the LL(1) parse table using those sets and display the FIRST sets, FOLLOW sets, and the parse table as a formatted matrix. Then parse the input string "id + id * id" with the table, showing each step with the parsing stack and the remaining input.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- E
- E'
- T
- T'
- F
- id
- +
- *
- (
- )
