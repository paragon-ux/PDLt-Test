# Wrong: get() does not refresh recency, so eviction is FIFO, not LRU.
import threading
from collections import OrderedDict


class ShardedLRUCache:
    def __init__(self, capacity=128, num_shards=16):
        self.locks = [threading.Lock() for _ in range(num_shards)]
        self.maps = [OrderedDict() for _ in range(num_shards)]
        self.capacity = capacity

    def get(self, key):
        i = hash(key) % len(self.maps)
        with self.locks[i]:
            return self.maps[i].get(key)

    def put(self, key, value):
        i = hash(key) % len(self.maps)
        with self.locks[i]:
            self.maps[i][key] = value
            if len(self.maps[i]) > self.capacity:
                self.maps[i].popitem(last=False)
