TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Diagnose the intermittent deadlock in the provided Python program that uses two locks (lock_a and lock_b) with opposite acquisition orders in transfer_ab and transfer_ba, explain the lock ordering violation, and supply a corrected version that avoids deadlock. Include a test that demonstrates the deadlock risk in the original code and verifies that the fixed code runs without hanging.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- lock_a
- lock_b
- transfer_ab
- transfer_ba
