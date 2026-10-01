DESIGN the skip list class structure in Python to serve as an ordered map.
GENERATE random node levels using a coin flip with probability 0.5, capped at level 16.
IMPLEMENT INSERT(key, value) to add a key-value pair while preserving ordering.
IMPLEMENT SEARCH(key) to retrieve the value associated with a given key.
IMPLEMENT DELETE(key) to remove a key and its value while preserving ordering.
IMPLEMENT RANGE_QUERY(lo, hi) to return all key-value pairs with keys in the inclusive range [lo, hi].
COMPOSE a test suite that:
  INSERT a sequence of keys and values.
  DELETE a subset of keys.
  VALIDATE ordering invariants after each batch of operations.
  PERFORM 1000 insertions, RECORD node levels, and ANALYZE the level distribution.
  EXECUTE range queries for varied lo and hi values and CONFIRM correct results.
OUTPUT the Python source code for the skip list implementation and the accompanying test suite.
