TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a thread-safe sharded LRU cache in Python. The cache is divided into N shards (default 16), each with its own lock and capacity. Keys are routed to shards via hash(key) % N. Each shard independently maintains LRU eviction order. No global lock is held during get() or put() operations. Include a multi-threaded stress test with 8 threads performing concurrent reads and writes, verifying no data corruption and correct eviction behavior.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- thread-safe sharded LRU cache
- Python
- N shards
- default 16
- hash(key) % N
- LRU eviction order
- get()
- put()
- multi-threaded stress test
- 8 threads
- concurrent reads and writes
- data corruption
- correct eviction behavior
