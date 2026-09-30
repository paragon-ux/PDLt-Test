TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Identify the race condition in the provided Python code where multiple threads increment a shared global variable 'counter' without synchronization, demonstrate that this can lead to an incorrect final count, and provide two fixes: (a) add a threading.Lock to protect the increment operation, and (b) use a thread‑safe alternative without an explicit lock, such as a multiprocessing.Value or collections.Counter with atomic updates. Include test code for both fixes that verifies the final count equals the expected 400000.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- counter
- increment
- threading.Lock
