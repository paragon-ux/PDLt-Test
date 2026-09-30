TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a counting Bloom filter in Python with the following capabilities: provide add(item), remove(item), and might_contain(item) operations; use k independent murmur-style hash functions; automatically compute optimal filter size m and number of hash functions k based on expected element count n and desired false positive rate p; include a test that inserts 10,000 items, verifies zero false negatives, measures the actual false positive rate over 10,000 non-member queries, and confirms the measured rate is within twice the theoretical bound.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- add(item)
- remove(item)
- might_contain(item)
- counting Bloom filter
- Python
- false positive rate
