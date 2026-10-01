TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Identify the race condition in the provided Python code where the global variable counter is incremented by multiple threads without synchronization, demonstrate that this can produce an incorrect final result (the printed value may be less than the expected 400000), and provide two corrected implementations: (a) modify the code to use a threading.Lock to protect the increment operation, ensuring atomic updates and confirming that the final printed output matches the expected 400000; (b) modify the code to avoid an explicit lock by employing a thread‑safe data structure or atomic‑like approach in Python (e.g., using a queue or other concurrency‑safe mechanism) to achieve correct counting, and also verify that the final printed output matches the expected 400000.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- threading.Lock
- counter
- increment
- 4
- 400000
- print
