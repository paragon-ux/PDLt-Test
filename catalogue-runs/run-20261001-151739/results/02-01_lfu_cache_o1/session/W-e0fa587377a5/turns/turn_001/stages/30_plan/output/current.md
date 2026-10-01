DEFINE appropriate data structures for O(1) get and put operations
CREATE a hash map mapping keys to nodes storing value, frequency, and position references
ORGANIZE nodes into doubly linked lists grouped by frequency, preserving insertion order for LRU tie-breaking
IMPLEMENT LFUCache class with __init__(capacity), get(key), and put(key, value) methods
IN get(key):
  IF key exists THEN retrieve node, INCREMENT its frequency, MOVE node to the higher-frequency list while preserving LRU order, RETURN its value
  ELSE RETURN a sentinel indicating a miss
IN put(key, value):
  IF capacity is zero THEN RETURN
  IF key exists THEN update its value and CALL get(key) to adjust frequency and position
  ELSE IF cache size equals capacity THEN IDENTIFY the lowest-frequency list, SELECT its LRU node, REMOVE the node from hash map and frequency list
  INSERT a new node with frequency 1 into the frequency-1 list and add it to the hash map
  UPDATE the tracker of the minimum frequency as needed
DEVELOP a self-contained test suite that
  INSTANTIATE an LFUCache with a chosen capacity
  EXECUTE a series of put and get operations to validate capacity enforcement, correct frequency updates, and proper LRU eviction when frequencies tie
  ASSERT that the cache returns expected values after each operation
RUN the test suite and confirm all assertions pass
