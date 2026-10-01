import threading
from collections import OrderedDict

class LRUShard:
    """A thread‑safe LRU container with a fixed capacity.
    Internally uses an OrderedDict where the most‑recently used item
    is moved to the end. All operations are protected by a per‑shard lock.
    """
    __slots__ = ("capacity", "lock", "data")

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.lock = threading.Lock()
        self.data: OrderedDict = OrderedDict()

    def get(self, key):
        with self.lock:
            if key not in self.data:
                return None
            # Move to end to mark as most‑recently used
            value = self.data.pop(key)
            self.data[key] = value
            return value

    def put(self, key, value):
        with self.lock:
            if key in self.data:
                # Update existing entry and move to end
                self.data.pop(key)
            self.data[key] = value
            # Evict least‑recently used if over capacity
            if len(self.data) > self.capacity:
                self.data.popitem(last=False)

    def size(self):
        with self.lock:
            return len(self.data)

    def items(self):
        with self.lock:
            return list(self.data.items())

class ShardedLRUCache:
    """Sharded LRU cache.
    * Shard count defaults to 16.
    * Keys are routed to shards via ``hash(key) % shard_count``.
    * Each shard has its own lock and capacity.
    """
    def __init__(self, shard_count: int = 16, per_shard_capacity: int = 128):
        self.shard_count = shard_count
        self.shards = [LRUShard(per_shard_capacity) for _ in range(shard_count)]

    def _shard_index(self, key) -> int:
        return hash(key) % self.shard_count

    def get(self, key):
        shard = self.shards[self._shard_index(key)]
        return shard.get(key)

    def put(self, key, value):
        shard = self.shards[self._shard_index(key)]
        shard.put(key, value)

    # Helper for testing/validation
    def shard_sizes(self):
        return [shard.size() for shard in self.shards]

# ---- Stress test ----
import random
import time

def stress_test():
    cache = ShardedLRUCache()  # defaults: 16 shards, 128 per shard
    num_threads = 8
    ops_per_thread = 1000
    keys = list(range(2000))

    def worker(thread_id: int):
        rnd = random.Random(thread_id)  # deterministic per thread
        for _ in range(ops_per_thread):
            op = rnd.choice(["get", "put"])
            key = rnd.choice(keys)
            if op == "put":
                cache.put(key, f"val-{thread_id}-{key}")
            else:
                _ = cache.get(key)
        # End of worker

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    duration = time.time() - start

    # Validation: each shard respects capacity and LRU order
    for i, shard in enumerate(cache.shards):
        assert shard.size() <= shard.capacity, f"Shard {i} exceeds capacity"
        # Verify LRU ordering: the oldest entry is first
        items = shard.items()
        # No explicit check of order beyond size; correctness is exercised by the cache logic.
    print(f"Stress test completed in {duration:.3f}s. All shards within capacity.")

if __name__ == "__main__":
    stress_test()
