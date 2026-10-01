IMPLEMENT a B+ tree data structure in Python
CONFIGURE the tree order to be configurable with default order 4
ENSURE all stored values reside in leaf nodes; internal nodes contain only routing keys
LINK leaf nodes via a doubly-linked list to enable efficient range scans
PROVIDE operation insert(key, value)
PROVIDE operation search(key)
PROVIDE operation range_scan(lo, hi)
ENABLE serialize capability for the entire tree
ENABLE deserialize capability for the entire tree
DEVELOP a test suite that verifies node splits on insertion, correctness of range_scan(lo, hi), and round‑trip fidelity of serialize and deserialize
