import hashlib
import math


class CountingBloomFilter:
    def __init__(self, expected_items, false_positive_rate):
        n, p = expected_items, false_positive_rate
        self.m = max(1, math.ceil(-n * math.log(p) / (math.log(2) ** 2)))
        self.k = max(1, round(self.m / n * math.log(2)))
        self.counts = [0] * self.m

    def _indexes(self, item):
        digest = hashlib.sha256(str(item).encode()).digest()
        h1 = int.from_bytes(digest[:8], "big")
        h2 = int.from_bytes(digest[8:16], "big") | 1
        return [(h1 + i * h2) % self.m for i in range(self.k)]

    def add(self, item):
        for i in self._indexes(item):
            self.counts[i] += 1

    def remove(self, item):
        if not self.might_contain(item):
            return False
        for i in self._indexes(item):
            self.counts[i] -= 1
        return True

    def might_contain(self, item):
        return all(self.counts[i] > 0 for i in self._indexes(item))
