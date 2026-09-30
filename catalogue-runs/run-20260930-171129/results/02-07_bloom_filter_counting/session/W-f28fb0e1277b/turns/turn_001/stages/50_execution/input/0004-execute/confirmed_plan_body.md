READ expected element count n and desired false positive rate p
COMPUTE optimal filter size m and number of hash functions k from n and p using standard Bloom filter formulas
IMPLEMENT a counting Bloom filter in Python that uses k independent murmur-style hash functions
DEFINE operation add(item) that hashes item with the k functions and increments the corresponding counters
DEFINE operation remove(item) that hashes item with the k functions and decrements the corresponding counters, ensuring counters do not drop below zero
DEFINE operation might_contain(item) that hashes item with the k functions and returns true only if all corresponding counters are greater than zero
CREATE a test harness that inserts 10,000 distinct items using add(item)
VERIFY that might_contain(item) returns true for all inserted items (zero false negatives)
QUERY 10,000 distinct non‑member items using might_contain(item) and record the number of positive responses
CALCULATE the observed false positive rate as (positive responses / 10,000)
COMPUTE the theoretical false positive bound from n, m, and k
CONFIRM that the observed false positive rate does not exceed twice the theoretical bound
