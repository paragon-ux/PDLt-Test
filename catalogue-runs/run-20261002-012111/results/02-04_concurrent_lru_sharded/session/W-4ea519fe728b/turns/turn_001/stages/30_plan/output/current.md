DESIGN the sharded LRU cache architecture.
DETERMINE the number of shards (default 16).
ALLOCATE a separate lock and capacity for each shard.
DEFINE the mapping of keys to shards using hash(key) % N.
SPECIFY per‑shard LRU eviction order using an appropriate data structure.
IMPLEMENT the get(key) operation to locate the shard, acquire its lock, retrieve the value, update LRU order, and release the lock.
IMPLEMENT the put(key, value) operation to locate the shard, acquire its lock, insert or update the entry, enforce capacity by evicting the least‑recently‑used entry if needed, and release the lock.
ENSURE that no global lock is used across shards.
CONSTRUCT a multi‑threaded stress test harness.
CREATE eight worker threads that perform a mix of get and put operations on the cache concurrently.
INVOCATE the stress test, allowing threads to run for a sufficient duration to exercise concurrent access patterns.
MONITOR for data corruption by checking consistency of retrieved values against expected entries.
ASSESS eviction correctness by verifying that entries exceeding per‑shard capacity are removed according to LRU order.
REPORT the test results indicating whether data integrity and eviction behavior are correct.
