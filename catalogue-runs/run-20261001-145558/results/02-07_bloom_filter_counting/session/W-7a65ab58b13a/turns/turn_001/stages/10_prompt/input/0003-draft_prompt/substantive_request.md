TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a counting Bloom filter in Python with the following requirements: support add(item), remove(item), and might_contain(item); use k independent murmur-style hash functions with a configurable false positive rate target; automatically calculate optimal filter size m and number of hash functions k given expected element count n and desired false positive rate p; include a test that inserts 10000 items, verifies zero false negatives, measures the actual false positive rate over 10000 non-member queries, and confirms it is within 2x of the theoretical bound.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- add(item)
- remove(item)
- might_contain(item)
- expected element count n
- desired false positive rate p
- 10000 items
- 10000 non-member queries

OPERATOR CORRECTION (host-side mechanical check): the following task entities are missing from the prompt body and MUST appear verbatim, character-for-character: add(item); remove(item); might_contain(item); expected element count n; desired false positive rate p; 10000 items; 10000 non-member queries
