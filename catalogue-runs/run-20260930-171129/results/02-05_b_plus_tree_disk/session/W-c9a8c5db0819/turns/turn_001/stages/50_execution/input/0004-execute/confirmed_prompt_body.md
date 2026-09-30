IMPLEMENT a B+ tree in Python with a configurable order (max children per node) default 4.
STORE all values exclusively in leaf nodes; INTERNAL nodes hold routing keys only.
LINK leaf nodes via a doubly-linked list to enable efficient range scans.
SUPPORT the operations insert(key, value), search(key), and range_scan(lo, hi).
PROVIDE page-level SERIALIZE to bytes and DESERIALIZE from bytes, preserving the tree structure and leaf links.
DELIVER a TEST SUITE that verifies insertion splits, correctness of range_scan results, and round‑trip fidelity of serialize/deserialize.
