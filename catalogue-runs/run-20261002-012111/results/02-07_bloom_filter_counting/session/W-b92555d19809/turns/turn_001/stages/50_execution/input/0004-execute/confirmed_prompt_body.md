IMPLEMENT a counting Bloom filter in Python
SUPPORT the methods add(item), remove(item), and might_contain(item)
USE k independent murmur-style hash functions
CONFIGURE a false positive rate target
CALCULATE the optimal filter size m automatically based on expected element count n and desired false positive rate p
PROVIDE a test that:
    INSERT 10000 items
    VERIFY zero false negatives
    MEASURE the actual false positive rate over 10000 non-member queries
    CONFIRM the observed false positive rate is within 2x of the theoretical bound
