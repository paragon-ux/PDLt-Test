TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a counting Bloom filter in Python that supports add(item), remove(item), and might_contain(item). Use k independent murmur-style hash functions with a configurable false positive rate target. Automatically calculate the optimal filter size m and number of hash functions k based on an expected element count n and desired false positive rate p. Provide a test that inserts 10000 items, verifies zero false negatives, measures the actual false positive rate over 10000 non-member queries, and confirms the measured false positive rate is within 2x of the theoretical bound.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Python
- add(item)
- remove(item)
- might_contain(item)
- k
- m
- n
- p
- 10000
- 2x
- murmur-style
