import threading
from collections import OrderedDict


class _Shard:
    def __init__(self, capacity):
        self.capacity = capacity
        self.lock = threading.Lock()
        self.data = OrderedDict()


class ShardedLRUCache:
    def __init__(self, capacity_per_shard=128, num_shards=16):
        self.shards = [_Shard(capacity_per_shard) for _ in range(num_shards)]

    def _shard(self, key):
        return self.shards[hash(key) % len(self.shards)]

    def get(self, key, default=None):
        shard = self._shard(key)
        with shard.lock:
            if key not in shard.data:
                return default
            shard.data.move_to_end(key)
            return shard.data[key]

    def put(self, key, value):
        shard = self._shard(key)
        with shard.lock:
            shard.data[key] = value
            shard.data.move_to_end(key)
            while len(shard.data) > shard.capacity:
                shard.data.popitem(last=False)
