IMPLEMENT a B+ tree in Python with configurable order (max children per node, default 4)
STORE all values in leaf nodes only
USE internal nodes to store keys for routing
LINK leaf nodes in a doubly‑linked list for efficient range scans
PROVIDE the following operations:
    INSERT(key, value)
    SEARCH(key)
    RANGE_SCAN(lo, hi)
INCLUDE page‑level serialization to bytes
INCLUDE deserialization that restores the exact tree structure
SUPPLY a test suite that verifies insertion splits, correct range‑scan results, and serialize/deserialize round‑trip fidelity
INCLUDE the following entities: B+ tree, Python, order, max children per node, default 4, values, leaf nodes, internal nodes, keys, routing, range scans, insert, search, range_scan, key, value, lo, hi, serialize, deserialize, bytes, test suite, insertion splits.
