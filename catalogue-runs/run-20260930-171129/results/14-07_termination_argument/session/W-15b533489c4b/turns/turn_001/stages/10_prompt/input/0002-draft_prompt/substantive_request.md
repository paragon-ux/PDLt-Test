TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Prove that the recursive function collatz_steps terminates for all non-negative integer inputs, where collatz_steps is defined as: if n <= 1 return 0; else if n is even return 1 + collatz_steps(n // 2); else return 1 + collatz_steps(3 * n + 1).
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- collatz_steps
