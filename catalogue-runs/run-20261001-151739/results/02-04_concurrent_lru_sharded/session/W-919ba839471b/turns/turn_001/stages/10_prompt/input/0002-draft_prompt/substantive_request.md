TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a thread-safe sharded LRU cache in Python, dividing the cache into N shards (default 16) each with its own lock and capacity, routing keys to shards via hash(key) % N, each shard independently maintaining LRU eviction order, ensuring no global lock is held during get() or put() operations, and include a multi-threaded stress test with 8 threads performing concurrent reads and writes to verify data integrity and correct eviction behavior.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- thread-safe sharded LRU cache
- Python
- N shards
- default 16
- hash(key) % N
- LRU eviction order
- global lock
- get()
- put()
- 8 threads
- capacity
