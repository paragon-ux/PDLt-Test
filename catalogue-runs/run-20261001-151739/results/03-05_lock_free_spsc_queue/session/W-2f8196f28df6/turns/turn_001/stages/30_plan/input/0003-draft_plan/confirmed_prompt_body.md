IMPLEMENT an SPSC lock‑free ring buffer in Python with fixed capacity N (where N is a power of 2).
DEFINE a push(item) method that RETURNS False when the buffer is full.
DEFINE a pop() method that RETURNS None when the buffer is empty.
USE only atomic‑style index reads/writes; DO NOT use locks or mutexes.
PROVIDE a test that LAUNCHES two threads:
    ONE thread PUSHES 100000 integers into the buffer.
    THE OTHER thread POPS items from the buffer.
VERIFY that all items are received in order with no duplicates or drops.
