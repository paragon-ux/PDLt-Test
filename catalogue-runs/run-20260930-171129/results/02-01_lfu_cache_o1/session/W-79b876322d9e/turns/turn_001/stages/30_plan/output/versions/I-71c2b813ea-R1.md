DEFINE a class LFUCache with constructor accepting capacity
INITIALIZE internal data structures: key‑to‑node map, frequency‑to‑ordered‑dict map, and minFrequency tracker
IMPLEMENT GET(key) operation:
IF key not in key‑to‑node map RETURN indicator for miss
RETRIEVE node, UPDATE its frequency using a helper that moves node to the next frequency list and updates minFrequency as needed
RETURN node value
IMPLEMENT PUT(key, value) operation:
IF capacity is zero RETURN immediately
IF key exists THEN update its value and treat as an access (invoke frequency update)
ELSE
IF current size equals capacity THEN EVICT the least frequently used key:
SELECT the ordered‑dict for minFrequency and REMOVE its oldest entry (LRU tie‑break)
DELETE the evicted key from key‑to‑node map
CREATE a new node with frequency 1, store in key‑to‑node map
ADD node to frequency‑to‑ordered‑dict under frequency 1
SET minFrequency to 1
DEVELOP a self‑contained test suite that:
INSTANTIATES LFUCache with a small capacity
PERFORMS a sequence of PUT and GET calls to validate:
capacity enforcement and eviction of correct key when cache is full
frequency increment on each GET and PUT access
LRU tie‑breaking when multiple keys share the minimum frequency
ASSERTS expected return values and internal state after each operation
PACKAGE the LFUCache class and its test suite as a single Python module
