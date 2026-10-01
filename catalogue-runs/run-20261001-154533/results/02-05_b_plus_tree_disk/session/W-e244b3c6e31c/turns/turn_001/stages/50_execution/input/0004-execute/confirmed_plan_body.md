DEFINE BPlusTree class with configurable order (default 4)
DEFINE internal node structure containing routing keys only
DEFINE leaf node structure extending internal node, containing values and prev/next pointers
LINK leaf nodes via a doubly‑linked list
IMPLEMENT insert(key, value) operation with logic for locating leaf, inserting entry, handling leaf overflow by splitting and propagating splits upward
IMPLEMENT search(key) operation that traverses internal nodes to leaf and returns associated value
IMPLEMENT range_scan(lo, hi) operation that locates starting leaf and iterates through linked leaf nodes emitting values within bounds
IMPLEMENT serialize() operation that traverses tree and records structure and data in a portable format
IMPLEMENT deserialize(data) operation that reconstructs tree structure and leaf linkage from the serialized representation
DEVELOP test suite:
  CREATE test case for insertion that triggers leaf node split and verifies structural correctness
  CREATE test case for insertion that causes internal node split and verifies tree height and routing keys
  CREATE test case for range_scan(lo, hi) verifying returned key‑value pairs match expected range
  CREATE test case for serialize followed by deserialize verifying that the deserialized tree yields identical search and range_scan results as original
