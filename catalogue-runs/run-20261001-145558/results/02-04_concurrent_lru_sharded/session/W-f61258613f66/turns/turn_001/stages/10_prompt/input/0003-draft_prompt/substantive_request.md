TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a thread-safe sharded LRU cache in Python with these requirements: the cache is divided into N shards (default 16), each with its own lock and capacity; keys are routed to shards via hash(key) % N; each shard independently maintains LRU eviction order; no global lock is held during get() or put() operations; include a multi-threaded stress test with 8 threads performing concurrent reads and writes, verifying no data corruption and correct eviction behavior.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- thread-safe
- sharded LRU cache
- Python
- N shards
- default 16
- lock
- capacity
- hash(key) % N
- LRU eviction order
- get()
- put()
- 8 threads
- concurrent reads and writes
- data corruption
- correct eviction behavior

OPERATOR CORRECTION (host-side mechanical check): the following task entities are missing from the prompt body and MUST appear verbatim, character-for-character: N shards
