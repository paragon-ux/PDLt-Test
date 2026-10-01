DEFINE the number of shards (default 16)
ALLOCATE a list of shard objects each with its own lock and capacity
IMPLEMENT an LRU data structure within each shard
ROUTE a key to its shard using hash(key) modulo number of shards
FOR each GET operation:
    ACQUIRE the lock of the target shard
    RETRIEVE the value and update LRU ordering within the shard
    RELEASE the shard lock
FOR each PUT operation:
    ACQUIRE the lock of the target shard
    INSERT or update the value, evict least-recently-used entry if capacity exceeded
    RELEASE the shard lock
ENSURE that no operation acquires more than one shard lock at a time
DEVELOP a multi-threaded stress test:
    SPAWN eight threads
    IN EACH thread, PERFORM a mix of GET and PUT operations on the shared cache
    TRACK inserted keys and expected values
    VERIFY that retrieved values match expectations (no data corruption)
    AFTER extensive operations, CONFIRM that eviction occurred per-shard according to LRU policy
RUN the stress test and COLLECT verification results
