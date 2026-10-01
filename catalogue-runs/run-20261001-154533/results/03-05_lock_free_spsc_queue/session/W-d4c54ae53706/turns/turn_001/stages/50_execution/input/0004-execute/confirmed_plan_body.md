DEFINE a lock‑free SPSC ring buffer class with fixed power‑of‑two capacity N
ALLOCATE a fixed‑size array of length N inside the class
INITIALIZE head and tail index variables to zero
IMPLEMENT push(item) method that:
    ATOMICALLY read head and tail
    COMPUTE next_head = (head + 1) AND (N - 1)
    IF next_head equals tail THEN return False
    STORE item at position head in the array
    ATOMICALLY update head to next_head
IMPLEMENT pop() method that:
    ATOMICALLY read head and tail
    IF head equals tail THEN return None
    READ item at position tail from the array
    ATOMICALLY update tail to (tail + 1) AND (N - 1)
    RETURN the retrieved item
CREATE a multithreaded test that:
    INSTANTIATE the ring buffer with appropriate capacity
    START a producer thread that pushes integers 0 through 99999 using push
    START a consumer thread that repeatedly calls pop and records received items
    WAIT for both threads to complete
VERIFY that the recorded sequence matches the original integer sequence exactly, confirming correct order and no duplicates or drops
OUTPUT the complete Python source code for the ring buffer implementation and the test harness
