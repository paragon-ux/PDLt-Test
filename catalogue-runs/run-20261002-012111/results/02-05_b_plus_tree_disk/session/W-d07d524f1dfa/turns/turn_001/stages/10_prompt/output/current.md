TASK ENTITIES: B+ tree, Python, order, 4, leaf nodes, internal nodes, keys, routing, doubly-linked list, insert, search, range_scan, serialize, deserialize, test suite
IMPLEMENT a B+ tree in Python with a CONFIGURABLE order (default 4)
STORE all values exclusively in leaf nodes with INTERNAL nodes holding only routing keys
LINK leaf nodes in a DOUBLY-LINKED LIST for efficient range scans
PROVIDE INSERT(key, value), SEARCH(key), and RANGE_SCAN(lo, hi) operations
ADD PAGE-LEVEL SERIALIZE and DESERIALIZE capabilities for the entire tree
CREATE a TEST SUITE that verifies insertion splits, range‑scan correctness, and serialize/deserialize round‑trip fidelity
