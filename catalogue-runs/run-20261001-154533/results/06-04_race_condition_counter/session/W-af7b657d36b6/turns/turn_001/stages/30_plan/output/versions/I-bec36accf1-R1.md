READ the provided Python script that uses a global variable 'counter' incremented by multiple threads
IDENTIFY the race condition in the script
DEMONSTRATE that the race condition can lead to an incorrect final counter value
GENERATE a corrected implementation (A) that synchronizes the increment operation with a threading.Lock
GENERATE a corrected implementation (B) that avoids explicit locks by employing a thread‑safe data structure or an atomic‑like counter
FOR each corrected implementation:
    INITIALIZE the counter to zero
    CREATE four threads, each performing one hundred thousand increments on the counter
    START the threads
    WAIT for all threads to complete
    READ the actual final counter value
    PRINT the expected total of four hundred thousand and the actual counter value
