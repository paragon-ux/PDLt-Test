CREATE a thread-safe sharded LRU cache implementation in Python.
DIVIDE the cache into N shards, default 16.
ASSIGN each shard its own lock and capacity.
ROUTE keys to shards using hash(key) % N.
MAINTAIN LRU eviction order within each shard.
ENSURE that no global lock is held during get() or put() operations.
INCLUDE a multi-threaded stress test with 8 threads that performs concurrent reads and writes.
    VERIFY that no data corruption occurs.
    VERIFY that eviction behavior is correct per shard.
