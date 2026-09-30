READ the provided Python code that increments a global counter from multiple threads
IDENTIFY the race condition affecting the global counter during concurrent increment operations
DEMONSTRATE that the race can produce an incorrect final count for the counter
SUPPLY a fix that protects the increment with a threading.Lock (using the entity threading.Lock and lock)
SUPPLY an alternative fix that uses a thread‑safe approach without an explicit lock, such as an atomic‑like construct or thread‑safe data structure (referencing atomic)
TEST both implementations and SHOW the expected versus actual counter values, including the counter and increment behavior
