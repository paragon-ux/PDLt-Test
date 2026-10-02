TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Diagnose the deadlock in the provided Python program that uses lock_a and lock_b in opposite acquisition order within transfer_ab and transfer_ba functions, explain the lock ordering violation, provide a corrected version that enforces a consistent lock acquisition order, and include a test that demonstrates the deadlock risk in the original code and verifies that the corrected code runs without hanging (using 100 threads for each direction and a join timeout of 5 seconds).
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- transfer_ab
- transfer_ba
- lock_a
- lock_b
- 100
- 5
- ab
- ba
- i
- join
- timeout
