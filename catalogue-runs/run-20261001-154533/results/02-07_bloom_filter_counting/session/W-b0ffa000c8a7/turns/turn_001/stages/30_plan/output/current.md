CALCULATE optimal filter size m and number of hash functions k from expected element count n and desired false positive rate p.
GENERATE k independent Murmur-style hash functions.
IMPLEMENT a Python class for a counting Bloom filter using an integer array of size m and the generated hash functions.
DEFINE the method add(item) that increments counters at the hashed positions.
DEFINE the method remove(item) that decrements counters at the hashed positions, ensuring counters do not become negative.
DEFINE the method might_contain(item) that checks whether all counters at hashed positions are greater than zero.
WRITE a test harness that creates an instance of the filter with the calculated parameters.
INSERT 10000 distinct items into the filter using the add method.
VERIFY that each inserted item returns true from might_contain (i.e., zero false negatives).
PERFORM 10000 queries on distinct non-member items using might_contain.
MEASURE the observed false positive rate from the non-member queries.
COMPARE the observed false positive rate to the theoretical bound derived from p.
CONFIRM that the observed rate is within twice the theoretical bound.
