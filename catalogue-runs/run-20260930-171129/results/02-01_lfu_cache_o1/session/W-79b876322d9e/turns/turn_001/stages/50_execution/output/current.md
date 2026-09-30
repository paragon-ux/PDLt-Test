# lfu_cache.py
"""Implementation of an LFU (Least Frequently Used) cache.
Both get(key) and put(key, value) run in O(1) average time.
When capacity is exceeded, the least frequently used key is evicted.
If several keys share the minimum frequency, the least recently used among them is evicted.
Access via get() or put() increments the usage frequency.
A self‑contained test suite validates capacity limits, frequency updates, and LRU tie‑breaking.
"""

from collections import defaultdict, OrderedDict

class LFUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.min_freq = 0
        self.key_node = {}  # key -> (value, freq)
        self.freq_dict = defaultdict(OrderedDict)  # freq -> keys in LRU order

    def _update(self, key: int):
        value, freq = self.key_node[key]
        # remove from current freq list
        del self.freq_dict[freq][key]
        if not self.freq_dict[freq]:
            del self.freq_dict[freq]
            if self.min_freq == freq:
                self.min_freq += 1
        # add to next freq list
        freq += 1
        self.freq_dict[freq][key] = None
        self.key_node[key] = (value, freq)
        return value

    def get(self, key: int):
        if key not in self.key_node:
            return -1
        return self._update(key)

    def put(self, key: int, value: int):
        if self.capacity == 0:
            return
        if key in self.key_node:
            # update value and treat as access
            _, freq = self.key_node[key]
            self.key_node[key] = (value, freq)
            self._update(key)
            return
        if len(self.key_node) >= self.capacity:
            # evict least frequently used, LRU within that freq
            evict_key, _ = self.freq_dict[self.min_freq].popitem(last=False)
            del self.key_node[evict_key]
            if not self.freq_dict[self.min_freq]:
                del self.freq_dict[self.min_freq]
        # insert new key with freq 1
        self.key_node[key] = (value, 1)
        self.freq_dict[1][key] = None
        self.min_freq = 1

# Self‑contained test suite
if __name__ == "__main__":
    def assert_equal(a, b, msg):
        if a != b:
            raise AssertionError(f"{msg}: {a} != {b}")

    # Test basic functionality and capacity eviction
    cache = LFUCache(2)
    cache.put(1, 1)        # cache: {1:1}
    cache.put(2, 2)        # cache: {1:1, 2:2}
    assert_equal(cache.get(1), 1, "GET 1 should return 1")  # freq(1)=2, freq(2)=1
    cache.put(3, 3)        # evicts key 2 (freq=1, LRU)
    assert_equal(cache.get(2), -1, "GET 2 should be miss after eviction")
    assert_equal(cache.get(3), 3, "GET 3 should return 3")
    assert_equal(cache.get(1), 1, "GET 1 should still return 1")

    # Test LRU tie‑breaking when frequencies are equal
    cache = LFUCache(3)
    cache.put(1, 10)
    cache.put(2, 20)
    cache.put(3, 30)
    # All frequencies are 1, order of insertion defines LRU
    cache.get(2)   # freq(2)=2
    cache.put(4, 40)  # should evict key 1 (freq=1, oldest)
    assert_equal(cache.get(1), -1, "Key 1 should be evicted (LRU tie)")
    assert_equal(cache.get(3), 30, "Key 3 should remain")
    assert_equal(cache.get(4), 40, "Key 4 should be present")

    print("All tests passed.")
