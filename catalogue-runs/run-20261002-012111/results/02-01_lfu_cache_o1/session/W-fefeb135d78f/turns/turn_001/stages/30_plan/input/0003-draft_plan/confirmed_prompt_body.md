IMPLEMENT a Least Frequently Used (LFU) cache in Python.
ENSURE that GET(key) and PUT(key, value) operate in O(1) average time complexity.
WHEN capacity is exceeded, EVICT the key with the lowest frequency.
IF multiple keys share the minimum frequency, EVICT the least recently used among them.
ON each GET(key) or PUT(key, value) access, INCREMENT the frequency count for that key.
INCLUDE a self-contained test suite that verifies capacity limits, frequency updates, and LRU tie-breaking.

- Python
- get(key)
- put(key, value)
- O(1)
- self-contained test suite
