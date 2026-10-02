IDENTIFY the race condition in the supplied Python code that increments a global counter via the function increment across four threading.Thread instances each invoking increment(100000)
ANALYZE how unsynchronized increments can cause the final counter to deviate from the expected value 400000
DEVISE a synchronized implementation that uses a threading.Lock to protect each increment operation
    IMPLEMENT acquisition of the lock immediately before updating the counter and release the lock after the update
    ENSURE the same lock object is shared by all thread instances
DEVISE a lock‑free implementation that employs a thread‑safe data structure or an atomic‑like counter abstraction in Python
    SELECT an appropriate thread‑safe construct (e.g., a multiprocessing.Value with lock disabled or a third‑party atomic integer)
    MODIFY the increment operation to update the counter through the chosen thread‑safe construct
FOR EACH implementation version, CREATE test code that exercises the multithreaded increment scenario
    DEFINE a test function that spawns four threads, each calling the respective increment implementation with 100000 iterations
    START all threads
    WAIT for all threads to complete
    PRINT the final counter value
    VERIFY that the printed value equals the expected 400000
