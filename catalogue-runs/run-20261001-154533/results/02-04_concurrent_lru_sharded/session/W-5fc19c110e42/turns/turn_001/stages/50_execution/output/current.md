import threading
import collections
import random
import time

class ShardLRUCache:
    """A thread‑safe LRU cache shard.
    Each shard has its own lock and capacity and maintains an OrderedDict
    (insertion order) where the most‑recently‑used entry is moved to the end.
    """
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.lock = threading.Lock()
        self.map = collections.OrderedDict()

    def get(self, key):
        with self.lock:
            if key not in self.map:
                return None
            # Move to end (most recent)
            value = self.map.pop(key)
            self.map[key] = value
            return value

    def put(self, key, value):
        with self.lock:
            if key in self.map:
                # Update existing entry
                self.map.pop(key)
            self.map[key] = value
            # Evict if over capacity
            if len(self.map) > self.capacity:
                self.map.popitem(last=False)  # pop least‑recently‑used

class ShardedLRUCache:
    """Sharded LRU cache with default 16 shards.
    Keys are routed to a shard via ``hash(key) % num_shards``.
    No global lock is used; only the shard's lock protects its data.
    """
    def __init__(self, per_shard_capacity: int, num_shards: int = 16):
        self.num_shards = num_shards
        self.shards = [ShardLRUCache(per_shard_capacity) for _ in range(num_shards)]

    def _get_shard(self, key):
        idx = hash(key) % self.num_shards
        return self.shards[idx]

    def get(self, key):
        shard = self._get_shard(key)
        return shard.get(key)

    def put(self, key, value):
        shard = self._get_shard(key)
        shard.put(key, value)

# ---------- Stress Test ----------

def stress_test():
    cache = ShardedLRUCache(per_shard_capacity=100, num_shards=16)
    num_threads = 8
    ops_per_thread = 5000
    keys_range = 2000
    # Shared record of expected values
    expected = {}
    lock = threading.Lock()

    def worker(thread_id: int):
        rnd = random.Random(thread_id)
        for _ in range(ops_per_thread):
            op = rnd.choice(["get", "put"])
            key = rnd.randint(0, keys_range)
            if op == "put":
                value = f"t{thread_id}-v{key}"
                cache.put(key, value)
                with lock:
                    expected[key] = value
            else:
                val = cache.get(key)
                with lock:
                    exp = expected.get(key)
                # Verify that the retrieved value matches expectation (or None)
                if val != exp:
                    raise AssertionError(f"Data corruption detected for key {key}: got {val}, expected {exp}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify eviction per shard: each shard should hold at most its capacity
    for i, shard in enumerate(cache.shards):
        if len(shard.map) > shard.capacity:
            raise AssertionError(f"Shard {i} exceeds capacity after test")
    print("Stress test completed successfully.")

if __name__ == "__main__":
    stress_test()
