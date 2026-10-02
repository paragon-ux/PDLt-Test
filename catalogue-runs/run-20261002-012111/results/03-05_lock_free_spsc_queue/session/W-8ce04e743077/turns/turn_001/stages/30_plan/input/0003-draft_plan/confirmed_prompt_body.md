IMPLEMENT a lock-free single-producer single-consumer (SPSC) ring buffer in Python with fixed capacity N (a power of 2)
DEFINE the push(item) method that writes the item using atomic index reads/writes and returns False when the buffer is full
DEFINE the pop() method that reads the next item using atomic index reads/writes and returns None when the buffer is empty
INCLUDE a multithreaded test with two threads
  CREATE a producer thread that pushes 100000 integers using push
  CREATE a consumer thread that pops items using pop
VERIFY that all items are received in order without duplicates or drops
