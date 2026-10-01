IMPLEMENT a counting Bloom filter in Python that supports add(item), remove(item), and might_contain(item).
USE k independent murmur-style hash functions.
CONFIGURE a false positive rate target.
CALCULATE optimal filter size m and number of hash functions k based on expected element count n and desired false positive rate p.
PROVIDE a test.
INSERT 10000 items.
VERIFY zero false negatives.
MEASURE false positive rate over 10000 non-member queries.
CONFIRM measured false positive rate is within 2x of the theoretical bound.
