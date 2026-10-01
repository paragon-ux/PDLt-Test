READ the provided Python script that uses a global variable 'counter' incremented by multiple threads
IDENTIFY the race condition in the script
DEMONSTRATE that the race condition can lead an incorrect final counter value
SUPPLY two corrected implementations:
  (A) SYNCHRONIZE the increment operation with a threading.Lock
  (B) AVOID explicit locks by employing a thread‑safe data structure or an atomic‑like counter
FOR each implementation:
  RUN 4 threads, each performing 100000 increments
  PRINT the expected total of 400000 and the actual counter value
