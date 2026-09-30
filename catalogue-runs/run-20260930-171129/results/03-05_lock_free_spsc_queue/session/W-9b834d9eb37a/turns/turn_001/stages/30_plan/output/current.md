DEFINE a RingBuffer class with fixed capacity N (power of 2) and internal array storage
INITIALIZE head and tail indices using atomic operations suitable for lock‑free access
IMPLEMENT push(item) to atomically check buffer fullness, write item, and advance tail without locks, returning False if full
IMPLEMENT pop() to atomically check buffer emptiness, read item, and advance head without locks, returning None if empty
CREATE a producer thread that iterates from 0 to 99,999 and calls push(item) for each integer
CREATE a consumer thread that repeatedly calls pop() and records retrieved items until 100,000 items have been collected
START both producer and consumer threads concurrently
WAIT for both threads to finish execution
VERIFY that the sequence of items retrieved by the consumer matches the original ordered range 0‑99,999 with no duplicates or missing values
