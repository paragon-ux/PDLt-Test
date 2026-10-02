TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a lock-free single-producer single-consumer (SPSC) ring buffer in Python with a fixed capacity N (a power of 2). Provide push(item) and pop() methods that use only atomic index reads/writes, where push returns False when the buffer is full and pop returns None when empty. Include a multithreaded test with two threads: one producer thread that pushes 100000 integers and one consumer thread that pops them, verifying that all items are received in order without duplicates or drops.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- SPSC
- Python
- N
- push(item)
- pop()
- push
- pop
- False
- None
- 100000
