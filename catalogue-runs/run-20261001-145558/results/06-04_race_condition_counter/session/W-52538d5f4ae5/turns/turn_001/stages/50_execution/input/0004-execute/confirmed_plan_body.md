IDENTIFY the race condition in the provided Python code that increments a global counter from multiple threads
DEMONSTRATE that the lack of synchronization can lead to an observed result different from the expected 400000
APPLY a threading.Lock to protect the increment operation
VERIFY the lock‑protected version by running the code and printing the expected and actual counter values
IMPLEMENT a lock‑free solution using a thread‑safe data structure or atomic‑like approach in Python
VERIFY the lock‑free version by running the code and printing the expected and actual counter values
