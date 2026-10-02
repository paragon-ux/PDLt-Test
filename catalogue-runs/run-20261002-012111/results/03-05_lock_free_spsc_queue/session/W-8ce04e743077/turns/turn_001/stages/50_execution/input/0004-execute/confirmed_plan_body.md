DEFINE the RingBuffer class with capacity N (power of 2)
SELECT atomic counter primitives for head and tail indices
INITIALIZE a storage array of length N inside the class
SET head and tail counters to zero
IMPLEMENT the push(item) method
    IF (head - tail) == N THEN RETURN False
    STORE item at index (head & (N-1))
    ATOMICALLY increment head
    RETURN True
IMPLEMENT the pop() method
    IF head == tail THEN RETURN None
    RETRIEVE item at index (tail & (N-1))
    ATOMICALLY increment tail
    RETURN the item
DEVISE a multithreaded test scenario
    CREATE a producer thread that pushes integers 0..99999 using push
    CREATE a consumer thread that repeatedly calls pop and records retrieved items
    WAIT for both threads to finish
    VERIFY that the recorded sequence contains exactly the integers 0..99999 in order without duplicates or losses
EXECUTE the test and OBSERVE verification outcome
