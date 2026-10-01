INITIALIZE a fixed-size array of capacity N (power of 2) to hold items.
INITIALIZE atomic head index = 0.
INITIALIZE atomic tail index = 0.
DEFINE push(item) method:
    READ tail index atomically.
    COMPUTE next_tail = (tail + 1) AND (N - 1).
    READ head index atomically.
    IF next_tail == head THEN
        RETURN False.
    ENDIF
    STORE item at position tail in the array.
    WRITE tail = next_tail atomically.
    RETURN True.
DEFINE pop() method:
    READ head index atomically.
    READ tail index atomically.
    IF head == tail THEN
        RETURN None.
    ENDIF
    READ item from position head in the array.
    COMPUTE next_head = (head + 1) AND (N - 1).
    WRITE head = next_head atomically.
    RETURN item.
CREATE a test harness:
    INSTANTIATE the buffer with a chosen power‑of‑2 capacity.
    CREATE thread A that iterates i from 0 to 99999 and calls push(i).
    CREATE thread B that repeatedly calls pop() until 100000 items have been collected.
    LAUNCH both threads concurrently.
    WAIT for both threads to complete.
    COLLECT popped items into a list.
    VERIFY that the list contains exactly the integers 0 through 99999 in order, without duplicates or omissions.
