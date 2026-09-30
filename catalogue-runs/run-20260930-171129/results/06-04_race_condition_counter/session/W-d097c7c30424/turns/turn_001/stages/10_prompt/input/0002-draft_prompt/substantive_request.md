TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Identify the race condition in the provided Python code that increments a global counter from multiple threads, demonstrate that the race can produce an incorrect final count, and supply two fixes: (a) protect the increment with a threading.Lock, and (b) use a thread‑safe alternative without an explicit lock, such as a thread‑safe data structure or atomic‑like approach in Python. Test both implementations and show the expected versus actual counter values.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- threading.Lock
- counter
- increment
- global
- lock
- atomic
