IMPLEMENT a Least Frequently Used (LFU) cache in Python.
ENSURE that both GET(key) and PUT(key, value) operations run in O(1) average time complexity.
WHEN the cache exceeds its capacity, EVICT the least frequently used key.
IF multiple keys share the minimum frequency, EVICT the least recently used among them.
ACCESSING a key via GET() OR UPDATING via PUT() MUST INCREMENT its usage frequency.
PROVIDE a self‑contained test suite that VERIFIES capacity limits, correct frequency updates, and LRU tie‑breaking behavior.
