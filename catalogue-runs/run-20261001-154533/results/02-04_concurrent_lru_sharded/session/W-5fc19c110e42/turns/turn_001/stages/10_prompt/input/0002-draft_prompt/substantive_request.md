TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Create a thread-safe sharded LRU cache implementation in Python. The cache must be divided into N shards (default 16), each with its own lock and capacity. Keys must be routed to shards using hash(key) % N. Each shard must maintain its own LRU eviction order. No global lock may be held during get() or put() operations. Additionally, include a multi‑threaded stress test with 8 threads that performs concurrent reads and writes, verifying that no data corruption occurs and that eviction behavior is correct per shard.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- thread-safe
- sharded LRU cache
- Python
- N
- default 16
- hash(key) % N
- LRU eviction order
- global lock
- get()
- put()
- 8 threads
