IMPLEMENT a thread-safe sharded LRU cache in Python.
DIVIDE the cache into N shards, default 16.
ASSIGN each shard a separate lock and capacity.
ROUTE keys to shards using hash(key) % N.
MAINTAIN LRU eviction order independently within each shard.
ENSURE get() and put() operations do NOT hold a global lock.
INCLUDE a multi-threaded stress test with 8 threads.
EXECUTE concurrent reads and writes.
VERIFY no data corruption.
VERIFY correct eviction behavior.
