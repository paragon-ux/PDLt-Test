ANALYZE the counting Bloom filter requirements
COMPUTE the optimal filter size m and number of hash functions k using the formulas m = - (n * ln(p)) / (ln(2)^2) and k = (m/n) * ln(2)
DESIGN an integer array of length m initialized to zero to serve as the counter table
GENERATE k independent murmur-style hash functions parameterized by distinct seeds
IMPLEMENT the method ADD(item) that:
    CALCULATE the k hash values for item
    MAP each hash to an index modulo m
    INCREMENT the counter at each index
IMPLEMENT the method REMOVE(item) that:
    CALCULATE the k hash values for item
    MAP each hash to an index modulo m
    DECREMENT the counter at each index, clamping at zero
IMPLEMENT the method MIGHT_CONTAIN(item) that:
    CALCULATE the k hash values for item
    MAP each hash to an index modulo m
    RETURN true only if all corresponding counters are greater than zero
DEVELOP a test suite that:
    INSERT 10,000 distinct items using ADD
    VERIFY that MIGHT_CONTAIN returns true for all inserted items (zero false negatives)
    QUERY 10,000 distinct non-member items using MIGHT_CONTAIN and RECORD the proportion of positive responses
    CONFIRM that the observed false positive rate is within twice the theoretical bound
EXECUTE the test suite and COLLECT verification results
PREPARE the final deliverable containing the Python implementation of the counting Bloom filter and the associated test script
