IMPLEMENT an LFU cache in Python
ENSURE get(key) and put(key, value) operate in O(1) average time
WHEN capacity is exceeded, EVICT the least frequently used key
IF multiple keys share the minimum frequency, EVICT the least recently used among them
INCREMENT frequency on each get(key) or put(key, value) access
INCLUDE a self-contained test suite verifying capacity limits, frequency updates, and LRU tie-breaking
