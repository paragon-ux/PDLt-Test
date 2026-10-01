PARSE the confirmed prompt body
DESIGN B+ tree data structures
    DEFINE internal node class with keys and child pointers
    DEFINE leaf node class with keys, values, previous leaf pointer, next leaf pointer
    SET configurable order parameter with default 4
IMPLEMENT INSERT(key, value)
    FIND the leaf node where the key belongs using internal routing keys
    INSERT key and value into leaf node in sorted order
    IF leaf node exceeds max entries THEN SPLIT leaf node
        CREATE a new leaf node
        DISTRIBUTE entries between the original and new leaf nodes
        UPDATE sibling pointers to link the new leaf into the doubly‑linked list
        PROPAGATE the split to the parent internal node
IMPLEMENT SEARCH(key)
    TRAVERSE internal nodes using routing keys to locate the target leaf node
    RETURN the associated value if present, otherwise indicate not found
IMPLEMENT RANGE_SCAN(lo, hi)
    FIND the first leaf node containing a key >= lo
    WHILE current leaf node contains keys <= hi
        COLLECT values whose keys fall within the range
        MOVE to the next leaf node via the doubly‑linked list
IMPLEMENT SERIALIZE_TREE()
    FOR each node in the tree in a deterministic order
        ENCODE node type, keys, child references, values, and sibling links into a byte representation
    CONCATENATE node byte blocks into a complete byte stream representing the tree
IMPLEMENT DESERIALIZE_TREE(byte_stream)
    READ node byte blocks sequentially
    RECREATE node objects with original properties
    REBUILD parent‑child relationships and sibling links to restore the exact tree structure
BUILD TEST_SUITE
    CREATE test case for insertion that triggers a leaf split
    CREATE test case for insertion that triggers an internal node split
    CREATE test case for SEARCH on existing and missing keys
    CREATE test case for RANGE_SCAN over multiple leaf nodes
    CREATE test case for SERIALIZE_TREE followed by DESERIALIZE_TREE confirming round‑trip fidelity
EXECUTE the test suite and VERIFY all tests pass
PACKAGE the Python implementation, serialization utilities, and test scripts as the final deliverable
