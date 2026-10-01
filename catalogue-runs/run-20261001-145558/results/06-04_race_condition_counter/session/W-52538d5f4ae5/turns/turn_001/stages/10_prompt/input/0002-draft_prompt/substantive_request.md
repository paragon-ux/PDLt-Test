TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Identify the race condition in the provided Python code that increments a global counter from multiple threads, demonstrate that the lack of synchronization can lead to an observed result different from the expected 400000, and provide two fixes: (a) introduce a threading.Lock to protect the increment operation, and (b) implement a lock‑free solution using a thread‑safe data structure or atomic‑like approach in Python. Verify both fixes by running the code and printing the expected and actual counter values.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- increment
- threading.Lock
- counter
- 4
- 400000
