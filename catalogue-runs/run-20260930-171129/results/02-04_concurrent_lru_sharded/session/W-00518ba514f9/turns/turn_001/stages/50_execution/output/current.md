# sharded_lru.py
import threading
import random
import time
from collections import defaultdict

class _Node:
    __slots__ = ('key', 'value', 'prev', 'next')
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None

class _Shard:
    def __init__(self, capacity):
        self.lock = threading.Lock()
        self.capacity = capacity
        self.map = {}  # key -> node
        # dummy head/tail for O(1) insert/remove
        self.head = _Node(None, None)  # most recent
        self.tail = _Node(None, None)  # least recent
        self.head.next = self.tail
        self.tail.prev = self.head
        self.size = 0

    def _add_front(self, node):
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node
        self.size += 1

    def _remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev
        self.size -= 1

    def _move_to_front(self, node):
        self._remove(node)
        self._add_front(node)

    def get(self, key):
        node = self.map.get(key)
        if node is None:
            return None
        self._move_to_front(node)
        return node.value

    def put(self, key, value):
        node = self.map.get(key)
        if node:
            node.value = value
            self._move_to_front(node)
        else:
            new_node = _Node(key, value)
            self._add_front(new_node)
            self.map[key] = new_node
            if self.size > self.capacity:
                # evict LRU (node before tail)
                lru = self.tail.prev
                self._remove(lru)
                del self.map[lru.key]

class ShardedLRUCache:
    def __init__(self, total_capacity, num_shards=16):
        self.num_shards = num_shards
        shard_cap = max(1, total_capacity // num_shards)
        self.shards = [_Shard(shard_cap) for _ in range(num_shards)]

    def _route(self, key):
        return hash(key) % self.num_shards

    def get(self, key):
        shard = self.shards[self._route(key)]
        with shard.lock:
            return shard.get(key)

    def put(self, key, value):
        shard = self.shards[self._route(key)]
        with shard.lock:
            shard.put(key, value)

# ------------------- Stress Test -------------------
def stress_test():
    total_capacity = 1000
    cache = ShardedLRUCache(total_capacity)
    key_space = list(range(200))
    # Track latest values per key for verification
    latest = {}
    stop_time = time.time() + 5  # run for 5 seconds

    def worker(thread_id):
        nonlocal latest
        while time.time() < stop_time:
            k = random.choice(key_space)
            op = random.choice(['get', 'put'])
            if op == 'put':
                v = f"val-{thread_id}-{random.randint(0, 100000)}"
                cache.put(k, v)
                latest[k] = v
            else:
                _ = cache.get(k)
        # end loop

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verification
    errors = []
    for k, expected in latest.items():
        actual = cache.get(k)
        if actual != expected:
            errors.append(f"Key {k} mismatch: expected {expected}, got {actual}")
    # Check shard capacities
    for idx, shard in enumerate(cache.shards):
        if shard.size > shard.capacity:
            errors.append(f"Shard {idx} over capacity: size {shard.size}, cap {shard.capacity}")
    if errors:
        print("TEST FAILED")
        for e in errors:
            print(e)
    else:
        print("TEST PASSED")

if __name__ == "__main__":
    stress_test()
