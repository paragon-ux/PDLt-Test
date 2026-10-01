OPERATIVE TASK ENTITIES: skip list, Python, ordered map interface, insert, search, delete, range_query, key, value, lo, hi, coin flip with p=0.5, p=0.5, max level 16, test suite, ordering invariants, probabilistic level distribution, 1000 insertions, range query results
DEFINE a skip list data structure in Python that implements an ordered map interface
DEFINE operation INSERT(key, value) to add a key-value pair
DEFINE operation SEARCH(key) to retrieve the value for a given key
DEFINE operation DELETE(key) to remove a key and its associated value
DEFINE operation RANGE_QUERY(lo, hi) to return all key-value pairs with keys in the inclusive range [lo, hi]
USE probabilistic level generation based on a COIN FLIP with p=0.5, limiting the maximum level to 16
ENSURE the skip list maintains ordering of keys for all operations
DEVELOP a TEST SUITE that:
  - VALIDATES ordering invariants after a series of insertions and deletions
  - ANALYZES probabilistic level distribution across 1000 insertions
  - CONFIRMS correct results of RANGE_QUERY for various lo and hi values
