IMPLEMENT a thread-safe sharded LRU cache in Python.
DIVIDE the cache into N shards, default 16.
ROUTE keys to shards using hash(key) % N.
ENSURE each shard has its own lock and capacity.
MAINTAIN LRU eviction order independently within each shard.
AVOID acquiring a global lock in get() and put() operations.
PROVIDE a multi-threaded stress test with 8 threads performing concurrent reads and writes to verify data integrity and correct eviction behavior.
RESPECT the per-shard capacity.
