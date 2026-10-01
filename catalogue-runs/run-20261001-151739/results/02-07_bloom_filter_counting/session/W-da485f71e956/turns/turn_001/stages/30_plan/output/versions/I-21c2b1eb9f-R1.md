VALIDATE that the expected element count n and target false positive rate p are specified.
CALCULATE optimal filter size m using the standard Bloom filter formula.
CALCULATE optimal number of hash functions k based on m and n.
INITIALIZE a counting array of length m with zero counters.
DEFINE k independent murmur-style hash functions that map items to indices in the range [0, m-1].
IMPLEMENT add(item) to increment the counters at the k hash positions for the item.
IMPLEMENT remove(item) to decrement the counters at the k hash positions for the item, preserving non-negative counter values.
IMPLEMENT might_contain(item) to return true only if all k counters at the hash positions are greater than zero, otherwise return false.
GENERATE a set of 10000 distinct items to serve as test inserts.
INSERT each test item using add(item).
VERIFY zero false negatives by checking that might_contain(item) returns true for every inserted item.
GENERATE a set of 10000 distinct non-member items to serve as false-positive queries.
MEASURE false positive rate by querying might_contain for each non-member item and computing the proportion of queries that incorrectly return true.
CALCULATE the theoretical false positive probability based on the computed m, k, and n.
COMPARE the measured false positive rate against twice the theoretical bound and confirm it satisfies the constraint.
REPORT the measured false positive rate and the verification outcome.
