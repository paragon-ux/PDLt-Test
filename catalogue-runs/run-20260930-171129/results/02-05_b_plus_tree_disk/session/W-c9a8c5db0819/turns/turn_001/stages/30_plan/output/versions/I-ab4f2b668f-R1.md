DEFINE BPlusTree class with configurable order (default 4)
INITIALIZE root as leaf node and maintain reference to first and last leaf
DEFINE Node base class with is_leaf flag, keys list, and parent reference
DEFINE LeafNode subclass of Node
STORE values list aligned with keys
INCLUDE prev and next pointers for doubly‑linked list
DEFINE InternalNode subclass of Node
STORE child pointers list aligned with keys
IMPLEMENT insert(key, value)
FIND target leaf via search traversal
INSERT key/value into leaf maintaining sorted order
IF leaf overflows (keys > order)
SPLIT leaf into two leaves
PROMOTE middle key to parent internal node
ADJUST doubly‑linked leaf pointers
RECURSIVELY handle internal node overflow
IMPLEMENT search(key)
TRAVERSE internal nodes using routing keys until leaf reached
RETURN associated value if key present, else indicate missing
IMPLEMENT range_scan(lo, hi)
FIND leaf containing lo via search traversal
ITERATE through leaf linked list from that leaf
YIELD (key, value) pairs while key <= hi
IMPLEMENT serialize()
PERFORM breadth‑first traversal of tree nodes
ENCODE node type, keys, and child/value references to bytes
INCLUDE leaf linkage information in serialized form
IMPLEMENT deserialize(byte_stream)
READ encoded nodes, reconstruct node objects and hierarchy
REBUILD parent pointers and leaf doubly‑linked list
DEVELOP test suite
TEST insertion causing leaf split and root split
TEST search for existing and non‑existing keys
TEST range_scan across multiple leaves
TEST serialize followed by deserialize yields identical tree structure and leaf links
VALIDATE that after deserialization, search and range_scan produce same results as before
