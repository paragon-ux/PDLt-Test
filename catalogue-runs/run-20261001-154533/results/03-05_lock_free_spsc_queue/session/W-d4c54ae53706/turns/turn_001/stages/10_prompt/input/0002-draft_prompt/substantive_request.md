TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Create a lock-free single-producer single-consumer (SPSC) ring buffer implementation in Python with a fixed power‑of‑two capacity N, providing push(item) and pop() operations that use only atomic index reads/writes without locks or mutexes. push must return False when the buffer is full and pop must return None when it is empty. Additionally, supply a multithreaded test with one producer thread pushing 100000 integers and one consumer thread popping them, verifying that all items are received in order without duplicates or drops.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Python
- push(item)
- pop()
- verifying that all items are received in order
