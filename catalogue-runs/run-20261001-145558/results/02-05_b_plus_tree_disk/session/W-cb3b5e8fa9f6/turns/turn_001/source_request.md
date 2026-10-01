Implement a B+ tree in Python with the following requirements:
1. Configurable order (max children per node), default 4.
2. All values stored in leaf nodes only; internal nodes store keys for routing.
3. Leaf nodes are linked in a doubly-linked list for efficient range scans.
4. Support insert(key, value), search(key), and range_scan(lo, hi).
5. Include page-level serialization: serialize the entire tree to bytes and deserialize it back, preserving structure.
6. Test suite verifying insertion splits, range scan correctness, and serialize/deserialize round-trip fidelity.
