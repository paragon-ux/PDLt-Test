IDENTIFY the race condition in the provided Python code where multiple threads increment the shared global variable 'counter' without synchronization.
DEMONSTRATE that this can lead to an incorrect final count when 4 threads each perform 100000 increments, resulting in a total less than 400000.
PROVIDE FIX (a): ADD a threading.Lock to protect the increment operation.
INCLUDE test code that creates a threading.Lock, wraps the increment of 'counter' with lock.acquire()/lock.release() (or with a context manager), runs 4 threads each performing 100000 increments, joins the threads, and ASSERT that the final value of 'counter' equals 400000.
PROVIDE FIX (b): USE a thread‑safe alternative without an explicit lock, such as a multiprocessing.Value or a collections.Counter (or similar atomic update mechanism).
INCLUDE test code that replaces the plain integer 'counter' with a multiprocessing.Value (or a thread‑safe Counter), runs the same 4 threads each performing 100000 increments, joins the threads, and ASSERT that the final count equals 400000.
ENSURE that both test scripts output the final count and confirm it matches the expected 400000.
