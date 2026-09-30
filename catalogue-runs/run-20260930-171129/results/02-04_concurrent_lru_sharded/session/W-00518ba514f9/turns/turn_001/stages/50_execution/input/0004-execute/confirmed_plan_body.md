INITIALIZE sharded LRU cache with N shards (default 16)
FOR each shard
CREATE independent lock
SET shard capacity = total_capacity / N
INITIALIZE empty doubly‑linked list for LRU order
INITIALIZE empty dictionary for key→node mapping
DEFINE function route_key(key) RETURN hash(key) % N
DEFINE get(key)
IDENTIFY shard = route_key(key)
ACQUIRE shard lock
IF key in shard dictionary THEN
MOVE node to front of shard LRU list
RETURN node value
ELSE
RETURN None
RELEASE shard lock
DEFINE put(key, value)
IDENTIFY shard = route_key(key)
ACQUIRE shard lock
IF key in shard dictionary THEN
UPDATE node value
MOVE node to front of shard LRU list
ELSE
CREATE new node with key and value
INSERT node at front of shard LRU list
ADD entry to shard dictionary
IF shard size > shard capacity THEN
REMOVE node at tail of shard LRU list
DELETE corresponding entry from shard dictionary
RELEASE shard lock
IMPLEMENT multithreaded stress test
INITIALIZE sharded LRU cache with total capacity (e.g., 1000)
SPAWN 8 threads
EACH thread repeatedly for a fixed duration
SELECT random key from shared key space
RANDOMLY choose operation get or put
PERFORM operation on cache
AFTER threads complete
VERIFY that for each key the cached value matches the most recent successful put
VERIFY that each shard’s size does not exceed its allocated capacity
REPORT any mismatches or capacity violations
