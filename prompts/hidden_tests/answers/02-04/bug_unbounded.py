# Wrong: never evicts, so the capacity is not enforced.
import threading


class ShardedLRUCache:
    def __init__(self, capacity=128, num_shards=16):
        self.locks = [threading.Lock() for _ in range(num_shards)]
        self.maps = [dict() for _ in range(num_shards)]

    def get(self, key):
        i = hash(key) % len(self.maps)
        with self.locks[i]:
            return self.maps[i].get(key)

    def put(self, key, value):
        i = hash(key) % len(self.maps)
        with self.locks[i]:
            self.maps[i][key] = value
