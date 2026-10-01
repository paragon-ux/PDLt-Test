DEFINE ring buffer structure with fixed capacity N as power of 2
INITIALIZE atomic head index and tail index to zero
IMPLEMENT push(item) operation
  READ current head and tail atomically
  CALCULATE next head position using modulo N
  IF next head equals tail THEN RETURN FALSE (buffer full)
  STORE item at head position
  UPDATE head index atomically
  RETURN TRUE
IMPLEMENT pop() operation
  READ current head and tail atomically
  IF head equals tail THEN RETURN NONE (buffer empty)
  RETRIEVE item at tail position
  UPDATE tail index atomically
  RETURN item
CREATE two threads
  THREAD 1 repeatedly CALL push(item) for integers 1 through 100000
  THREAD 2 repeatedly CALL pop() and record received items until 100000 items are collected
WAIT for both threads to complete
VERIFY that the recorded sequence contains exactly 100000 items in ascending order with no duplicates or gaps
