# Wrong: among equal frequencies it evicts the MOST recently used key.
from collections import OrderedDict, defaultdict


class LFUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.values, self.freq = {}, {}
        self.buckets = defaultdict(OrderedDict)

    def _touch(self, key):
        f = self.freq[key]
        del self.buckets[f][key]
        self.freq[key] = f + 1
        self.buckets[f + 1][key] = None

    def get(self, key):
        if key not in self.values:
            return -1
        self._touch(key)
        return self.values[key]

    def put(self, key, value):
        if key in self.values:
            self.values[key] = value
            self._touch(key)
            return
        if len(self.values) >= self.capacity:
            low = min(f for f, b in self.buckets.items() if b)
            victim, _ = self.buckets[low].popitem(last=True)
            del self.values[victim], self.freq[victim]
        self.values[key] = value
        self.freq[key] = 1
        self.buckets[1][key] = None
