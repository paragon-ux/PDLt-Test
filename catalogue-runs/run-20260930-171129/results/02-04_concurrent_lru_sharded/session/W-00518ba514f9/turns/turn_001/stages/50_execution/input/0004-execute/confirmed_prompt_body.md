CREATE a thread‑safe sharded LRU cache in Python with N shards (default 16)
FOR each shard, INITIALIZE an independent lock and a capacity equal to total_capacity / N
ROUTE each key to a shard using hash(key) % N
WITHIN each shard, MAINTAIN its own LRU eviction order using a doubly‑linked list and a dictionary
IMPLEMENT get(key):
IDENTIFY the target shard
ACQUIRE the shard's lock
IF key exists in shard, MOVE the entry to the front of the shard's LRU list and RETURN the value
ELSE RETURN None
RELEASE the shard's lock
IMPLEMENT put(key, value):
IDENTIFY the target shard
ACQUIRE the shard's lock
IF key exists, UPDATE the value and MOVE the entry to the front of the LRU list
ELSE INSERT the entry at the front of the LRU list
IF shard size exceeds its capacity, EVICT the least‑recently‑used entry from that shard
RELEASE the shard's lock
PROVIDE a multi‑threaded stress test:
INITIALIZE the sharded LRU cache with a reasonable total capacity (e.g., 1000 entries)
SPAWN 8 concurrent threads
EACH thread performs a random mix of get and put operations on shared keys for a fixed duration
AFTER all threads complete, VERIFY that no data corruption occurred (all retrieved values match the most recent puts) and that eviction has respected per‑shard capacity limits
REPORT any inconsistencies or eviction violations
