TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Identify the race condition in the provided Python script that uses a global variable 'counter' incremented by multiple threads, demonstrate that the race condition can lead to an incorrect final counter value, and supply two corrected implementations: (a) a version that synchronizes the increment operation with a threading.Lock, and (b) a version that avoids explicit locks by employing a thread‑safe data structure or an atomic‑like counter in Python. Each implementation should run four threads, each performing 100000 increments, and print both the expected total of 400000 and the actual counter value.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- counter
- increment
- 100000
- 4
- 400000
- threading.Lock
