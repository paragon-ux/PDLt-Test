IMPLEMENT a single-producer single-consumer (SPSC) lock-free ring buffer in Python with fixed capacity N (power of 2).
DEFINE push(item) operation that uses only atomic-style index reads/writes and returns FALSE when the buffer is full.
DEFINE pop() operation that uses only atomic-style index reads/writes and returns NONE when the buffer is empty.
ENSURE that push and pop preserve FIFO order without duplicates, drops, or reordering.
CREATE a test scenario using two threads:
  THREAD 1 pushes 100000 integers into the buffer using push.
  THREAD 2 pops items from the buffer using pop.
VERIFY that all 100000 items are received in the exact order they were pushed, with no duplicates or missing values.
INCLUDE only the above operative instructions; do not provide implementation code or execution results.
