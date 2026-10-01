import threading
import collections
import random
import time

class ShardLRUCache:
    """A single shard LRU cache with its own lock."""
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.lock = threading.Lock()
        self.map = {}  # key -> (value, node)
        self.order = collections.OrderedDict()  # key -> None, maintains recency

    def get(self, key):
        with self.lock:
            if key not in self.map:
                return None
            value, _ = self.map[key]
            # move to end to mark as recently used
            self.order.move_to_end(key)
            return value

    def put(self, key, value):
        with self.lock:
            if key in self.map:
                # update value and move to end
                self.map[key] = (value, None)
                self.order.move_to_end(key)
            else:
                if len(self.map) >= self.capacity:
                    # evict least recently used
                    eldest_key, _ = self.order.popitem(last=False)
                    del self.map[eldest_key]
                self.map[key] = (value, None)
                self.order[key] = None

class ShardedLRUCache:
    def __init__(self, shard_count: int = 16, shard_capacity: int = 128):
        self.shard_count = shard_count
        self.shards = [ShardLRUCache(shard_capacity) for _ in range(shard_count)]

    def _shard(self, key):
        return self.shards[hash(key) % self.shard_count]

    def get(self, key):
        return self._shard(key).get(key)

    def put(self, key, value):
        self._shard(key).put(key, value)

# Stress test
def stress_test():
    cache = ShardedLRUCache(shard_count=16, shard_capacity=64)
    stop_event = threading.Event()
    errors = []
    def worker(tid):
        rng = random.Random(tid)
        while not stop_event.is_set():
            op = rng.choice(["get", "put"])
            key = rng.randint(0, 200)
            if op == "put":
                cache.put(key, f"val-{tid}-{key}")
            else:
                _ = cache.get(key)
            # occasional consistency check
            if rng.random() < 0.001:
                # check that each shard's order size does not exceed capacity
                for shard in cache.shards:
                    if len(shard.map) > shard.capacity:
                        errors.append("capacity violation")
                        stop_event.set()
                        break
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for th in threads:
        th.start()
    # run for a short while
    time.sleep(2)
    stop_event.set()
    for th in threads:
        th.join()
    if errors:
        print("Errors detected:", errors)
    else:
        print("Stress test completed without corruption.")

if __name__ == "__main__":
    stress_test()
