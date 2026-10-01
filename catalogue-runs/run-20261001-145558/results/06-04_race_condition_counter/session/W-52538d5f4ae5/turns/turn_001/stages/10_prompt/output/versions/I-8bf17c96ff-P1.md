IDENTIFY the race condition in the provided Python code that increments a global counter from multiple threads.
DEMONSTRATE that the lack of synchronization can lead to an observed result different from the expected 400000.
PROVIDE two fixes:
  (a) INTRODUCE a threading.Lock to protect the increment operation.
  (b) IMPLEMENT a lock‑free solution using a thread‑safe data structure or atomic‑like approach in Python.
VERIFY both fixes by running the code and printing the expected and actual counter values.
INCLUDE the operative task entities exactly as listed: increment, threading.Lock, counter, 4, 400000.
