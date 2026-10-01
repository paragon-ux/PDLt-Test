TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a single-producer single-consumer (SPSC) lock‑free ring buffer in Python with a fixed capacity N (where N is a power of 2). Provide a push(item) method that returns False when the buffer is full and a pop() method that returns None when the buffer is empty, using only atomic‑style index reads/writes (no locks or mutexes). Include a test that launches two threads: one thread pushes 100000 integers into the buffer, the other thread pops them, verifying that all items are received in order with no duplicates or drops.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- SPSC
- push(item)
- pop()
- N
- 100000
