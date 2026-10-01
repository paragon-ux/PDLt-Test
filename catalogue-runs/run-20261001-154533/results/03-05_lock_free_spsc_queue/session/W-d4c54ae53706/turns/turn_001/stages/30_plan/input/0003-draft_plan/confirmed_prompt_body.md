CREATE a lock‑free single‑producer single‑consumer (SPSC) ring buffer implementation in Python with a fixed power‑of‑two capacity N.
DEFINE push(item) operation that enqueues an item, returning False if the buffer is full.
DEFINE pop() operation that dequeues the next item, returning None if the buffer is empty.
USE only atomic reads and writes of index variables; DO NOT employ locks or mutexes.
PROVIDE a multithreaded test where ONE producer thread pushes 100000 integers into the buffer and ONE consumer thread pops them.
VERIFY that all items are received in order without duplicates or drops (verifying that all items are received in order).
