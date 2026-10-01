IMPLEMENT a counting Bloom filter in Python supporting add(item), remove(item), and might_contain(item).
USE k independent murmur-style hash functions with a configurable false positive rate target.
CALCULATE optimal filter size m and number of hash functions k automatically given expected element count n and desired false positive rate p.
INCLUDE a test that inserts 10000 items, verifies zero false negatives, measures the actual false positive rate over 10000 non-member queries, and confirms it is within 2x of the theoretical bound.
ENSURE the implementation and test adhere to the specified operative task entities.
