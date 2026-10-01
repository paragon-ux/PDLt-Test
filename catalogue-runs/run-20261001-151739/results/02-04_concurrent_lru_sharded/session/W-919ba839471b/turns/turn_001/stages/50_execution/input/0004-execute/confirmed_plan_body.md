DETERMINE shard count (default 16) and per-shard capacity
DEFINE Shard abstraction
    CREATE a lock for the shard
    INITIALIZE an LRU container with the defined capacity
IMPLEMENT get operation
    CALCULATE shard index as hash(key) modulo shard count
    ACQUIRE lock of the target shard
    LOOKUP key in the shard's LRU container
    IF key found
        MOVE entry to most-recently-used position
        RETURN associated value
    ELSE
        RETURN miss indicator
    RELEASE shard lock
IMPLEMENT put operation
    CALCULATE shard index as hash(key) modulo shard count
    ACQUIRE lock of the target shard
    INSERT or UPDATE entry in the shard's LRU container
    MOVE entry to most-recently-used position
    IF shard size exceeds capacity
        EVICT least-recently-used entry
    RELEASE shard lock
COMPOSE Sharded LRU cache
    INSTANTIATE array of shards
    EXPOSE get and put methods delegating to respective shard operations
AVOID acquiring any global lock across shards
DESIGN multi-threaded stress test
    INSTANTIATE cache with default parameters
    CREATE eight worker threads
    ASSIGN each thread a random mix of get and put operations
    START all threads concurrently
    WAIT for all threads to finish
    VALIDATE that each shard respects its capacity
    VALIDATE that eviction within each shard follows LRU order
    RECORD any data integrity violations
REPORT test outcomes
