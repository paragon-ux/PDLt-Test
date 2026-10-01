DEFINE B+ tree class with configurable order (default 4)
INITIALIZE tree with a single leaf node as root
IMPLEMENT INSERT(key, value)
  LOCATE appropriate leaf node via internal routing keys
  INSERT key and value into leaf
  IF leaf exceeds capacity THEN SPLIT leaf
    CREATE new leaf node, redistribute entries, update doubly‑linked list
    PROMOTE split key to parent internal node
    IF parent exceeds capacity THEN SPLIT parent recursively
IMPLEMENT SEARCH(key)
  TRAVERSE internal nodes using routing keys to reach leaf
  RETURN associated value if key present
IMPLEMENT RANGE_SCAN(lo, hi)
  LOCATE leaf containing lo key
  ITERATE through doubly‑linked leaf list collecting entries whose keys lie between lo and hi
IMPLEMENT SERIALIZE()
  PERFORM page‑level traversal of tree nodes
  CONVERT each node (including keys, values, child pointers, and leaf links) to bytes preserving structure
IMPLEMENT DESERIALIZE(byte_stream)
  READ bytes to reconstruct node objects
  REESTABLISH parent‑child relationships and leaf doubly‑linked list
CREATE test suite
  INCLUDE test inserting keys that trigger leaf splits and verify correct parent routing keys
  INCLUDE test inserting keys that cause internal node splits and verify tree height updates
  INCLUDE test RANGE_SCAN across multiple leaves for correctness
  INCLUDE test SERIALIZE followed by DESERIALIZE and confirm tree equivalence
