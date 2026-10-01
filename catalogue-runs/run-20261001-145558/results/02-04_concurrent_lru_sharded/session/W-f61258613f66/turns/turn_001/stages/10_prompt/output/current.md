READ request to implement a thread-safe sharded LRU cache in Python.
SET default number of shards to 16.
DIVIDE the cache into N shards, each with its own lock and capacity.
ROUTE keys to shards using hash(key) % N.
MAINTAIN LRU eviction order independently within each shard.
ENSURE get() and put() operations acquire only the lock of the target shard, never a global lock.
INCLUDE a multi-threaded stress test with 8 threads performing concurrent reads and writes.
VERIFY that no data corruption occurs and that eviction behavior is correct.
