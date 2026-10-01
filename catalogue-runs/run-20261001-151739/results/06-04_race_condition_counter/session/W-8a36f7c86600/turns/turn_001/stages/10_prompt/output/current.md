IDENTIFY the race condition in the supplied Python code where the global variable counter is incremented by multiple threads without synchronization.
DEMONSTRATE that the race condition can produce an incorrect final result, where the print output may be less than 400000.
PROVIDE a corrected implementation that uses threading.Lock to protect each increment of counter, ensuring atomic updates, and CONFIRM that running the code with 4 threads results in the printed value equal to 400000.
PROVIDE an alternative corrected implementation that avoids an explicit lock by employing a thread‑safe data structure or atomic‑like approach (e.g., using a queue or other concurrency‑safe mechanism) to achieve correct counting, and CONFIRM that running the code with 4 threads results in the printed value equal to 400000.
USE the entities threading.Lock, counter, increment, 4, 400000, and print exactly as specified.
