PARSE the supplied Python code
ANALYZE the increments of the global variable counter
DETECT the unsynchronized increments across multiple threads
IDENTIFY the race condition caused by non‑atomic read‑modify‑write operations
SIMULATE execution with 4 threads to illustrate that the final printed value may be less than 400000
DESIGN a corrected implementation that uses threading.Lock
    CREATE a threading.Lock instance
    WRAP each counter increment within lock acquire and release
IMPLEMENT the corrected code using the lock‑protected increments
EXECUTE the lock‑protected implementation with 4 threads
CONFIRM that the printed counter equals 400000
DESIGN an alternative corrected implementation without an explicit lock
    SELECT a thread‑safe data structure or atomic‑like mechanism (e.g., queue or multiprocessing.Value)
    REPLACE the global counter with the chosen thread‑safe construct
    ENSURE each increment operation interacts with the thread‑safe construct atomically
IMPLEMENT the alternative thread‑safe implementation
EXECUTE the alternative implementation with 4 threads
CONFIRM that the printed counter equals 400000
