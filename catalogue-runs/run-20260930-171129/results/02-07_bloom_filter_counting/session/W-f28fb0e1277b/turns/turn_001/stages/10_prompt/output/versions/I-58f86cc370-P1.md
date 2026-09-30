READ expected element count n and desired false positive rate p
COMPUTE optimal filter size m and number of hash functions k based on n and p
IMPLEMENT a counting Bloom filter in Python using k independent murmur-style hash functions
PROVIDE the following operations on the filter: add(item), remove(item), might_contain(item)
INCLUDE a test that inserts 10,000 distinct items, verifies zero false negatives, queries 10,000 non‑member items, measures the actual false positive rate, and CONFIRMS that the measured rate is no more than twice the theoretical bound
