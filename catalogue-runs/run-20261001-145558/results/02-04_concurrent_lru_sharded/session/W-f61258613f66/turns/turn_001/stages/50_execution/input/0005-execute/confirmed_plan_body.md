DESIGN the cache structure with N shards and per‑shard lock
SET default shard count to 16
IMPLEMENT each shard as an LRU container with its own capacity limit
DEFINE a hash function to map keys to shard index via hash(key) % N
WRITE get(key) to locate target shard, acquire its lock, retrieve value, update LRU order, and release lock
WRITE put(key, value) to locate target shard, acquire its lock, insert or update entry, enforce per‑shard capacity by evicting least‑recently‑used items, and release lock
COMPOSE a Cache class that delegates get and put to appropriate shards
DEVELOP a multi‑threaded stress test that creates 8 threads each performing a mix of get and put operations on shared Cache instance
INSTRUMENT the test to record any data corruption or inconsistent state
RUN the stress test and VERIFY that no corruption occurs and that eviction behavior matches expected LRU policy
