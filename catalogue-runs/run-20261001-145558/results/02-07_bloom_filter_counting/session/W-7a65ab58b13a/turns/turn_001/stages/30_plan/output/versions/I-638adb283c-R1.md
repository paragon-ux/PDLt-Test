CALCULATE optimal filter size m and number of hash functions k given expected element count n and desired false positive rate p
INITIALIZE a counting Bloom filter with size m and k hash functions
IMPLEMENT add(item) to increment counters at hashed positions
IMPLEMENT remove(item) to decrement counters at hashed positions
IMPLEMENT might_contain(item) to check that all hashed counters are non‑zero
GENERATE 10000 unique test items
INSERT each test item into the filter using add(item)
VERIFY zero false negatives by confirming might_contain(item) is true for all inserted items
GENERATE another 10000 distinct non‑member items
QUERY the filter with might_contain(item) for each non‑member item and record false positives
COMPUTE actual false positive rate as (false positives / 10000)
COMPARE actual false positive rate to theoretical bound and confirm it is within twice the bound
