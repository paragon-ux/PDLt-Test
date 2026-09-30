IMPLEMENT a single-producer single-consumer lock‑free ring buffer in Python with fixed capacity N (power of 2)
PROVIDE push(item) that returns False when the buffer is full
PROVIDE pop() that returns None when the buffer is empty
INCLUDE a test using two threads
CREATE a producer thread that pushes 100000 integers into the buffer via push(item)
CREATE a consumer thread that repeatedly calls pop() until it has retrieved all items
VERIFY that the consumer receives all integers in the original order with no duplicates or drops
