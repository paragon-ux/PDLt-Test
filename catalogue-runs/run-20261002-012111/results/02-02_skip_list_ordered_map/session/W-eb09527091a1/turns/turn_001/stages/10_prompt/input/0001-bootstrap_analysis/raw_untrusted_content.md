Implement a skip list in Python that supports an ordered map interface with the following operations:
- insert(key, value): Insert or update a key-value pair
- search(key): Return the value for a key, or None
- delete(key): Remove a key
- range_query(lo, hi): Return all key-value pairs where lo <= key <= hi

Use probabilistic level generation (coin flip with p=0.5, max level 16). Include a test suite that verifies ordering invariants, probabilistic level distribution over 1000 insertions, and correct range query results.
