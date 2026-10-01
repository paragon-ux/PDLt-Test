IMPLEMENT a counting Bloom filter in Python.
SUPPORT the functions add(item), remove(item), and might_contain(item).
USE k independent murmur-style hash functions.
TARGET a false positive rate p.
CALCULATE optimal filter size m and number of hash functions k from expected element count n and desired false positive rate p.
INCLUDE a test that INSERTS 10000 items, VERIFIES zero false negatives, MEASURES the actual false positive rate over 10000 non-member queries, and CONFIRMS it is within 2x of the theoretical bound.
