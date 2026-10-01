TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Diagnose the intermittent deadlock in the provided Python program caused by inconsistent lock ordering between transfer_ab (acquires lock_a then lock_b) and transfer_ba (acquires lock_b then lock_a). Explain the lock ordering violation, and supply a corrected version where both functions acquire the locks in a consistent global order to prevent deadlock. Include a test that demonstrates the deadlock risk in the original code and verifies that the fixed code runs without hanging.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- transfer_ab
- transfer_ba
- lock_a
- lock_b
- deadlock
- lock ordering
