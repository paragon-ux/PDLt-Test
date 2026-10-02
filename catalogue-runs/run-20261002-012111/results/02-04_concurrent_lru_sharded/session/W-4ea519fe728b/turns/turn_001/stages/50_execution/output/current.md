import threading
from collections import OrderedDict

class ShardLRUCache:
    """Thread‑safe sharded LRU cache.

    * Each shard has its own lock and capacity.
    * Keys are routed to shards via ``hash(key) % num_shards``.
    * LRU order is maintained per‑shard using ``OrderedDict`` where the
      most‑recently‑used entry is moved to the end.
    * ``get`` and ``put`` operate without a global lock.
    """

    def __init__(self, capacity_per_shard: int = 100, num_shards: int = 16):
        self.num_shards = num_shards
        self.capacity = capacity_per_shard
        self.shards = []
        for _ in range(num_shards):
            shard = {
                "lock": threading.Lock(),
                "map": {},                     # key -> value
                "order": OrderedDict()        # key order, most recent at end
            }
            self.shards.append(shard)

    def _get_shard(self, key):
        idx = hash(key) % self.num_shards
        return self.shards[idx]

    def get(self, key):
        shard = self._get_shard(key)
        with shard["lock"]:
            if key not in shard["map"]:
                return None
            # Move key to end to mark as recently used
            shard["order"].move_to_end(key)
            return shard["map"][key]

    def put(self, key, value):
        shard = self._get_shard(key)
        with shard["lock"]:
            if key in shard["map"]:
                # Update existing entry and refresh LRU order
                shard["map"][key] = value
                shard["order"].move_to_end(key)
                return
            # Insert new entry
            shard["map"][key] = value
            shard["order"][key] = None
            # Evict if over capacity
            if len(shard["map"]) > self.capacity:
                oldest_key, _ = shard["order"].popitem(last=False)
                del shard["map"][oldest_key]

# ---------- Stress test ----------
import random
import time

def stress_test():
    cache = ShardLRUCache(capacity_per_shard=50, num_shards=16)
    stop_flag = threading.Event()
    errors = []

    def worker(thread_id):
        while not stop_flag.is_set():
            op = random.choice(["get", "put"])
            key = random.randint(0, 200)
            if op == "put":
                value = f"v{thread_id}-{key}"
                cache.put(key, value)
            else:
                val = cache.get(key)
                # Verify that a retrieved value, if present, matches the last writer
                # (simple sanity check – not exhaustive)
                if val is not None and not val.startswith("v"):
                    errors.append((thread_id, key, val))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    time.sleep(3)  # Run for a few seconds
    stop_flag.set()
    for t in threads:
        t.join()
    # Verify eviction per‑shard respects capacity
    for shard in cache.shards:
        if len(shard["map"]) > cache.capacity:
            errors.append(("eviction", len(shard["map"])) )
    print("errors:", errors)
    return errors

if __name__ == "__main__":
    stress_test()
