TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a single-producer single-consumer (SPSC) lock-free ring buffer in Python with a fixed capacity N (power of 2). Provide push(item) and pop() operations that use only atomic-style index reads/writes without locks or mutexes. push should return False when the buffer is full; pop should return None when empty. Include a test using two threads: one thread pushes 100000 integers, the other thread pops them, verifying that all items are received in order with no duplicates or drops.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- push
- pop
- N
- 100000

OPERATOR CORRECTION (host-side mechanical check): the following task entities are missing from the prompt body and MUST appear verbatim, character-for-character: push; pop
