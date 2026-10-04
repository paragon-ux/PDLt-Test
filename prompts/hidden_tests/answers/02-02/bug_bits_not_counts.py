# Wrong: a plain bit array, so remove() clears bits other members share.
import hashlib
import math


class CountingBloomFilter:
    def __init__(self, expected_items, false_positive_rate):
        self.m = math.ceil(-expected_items * math.log(false_positive_rate) / math.log(2) ** 2)
        self.k = max(1, round(self.m / expected_items * math.log(2)))
        self.bits = [False] * self.m

    def _idx(self, item):
        d = hashlib.md5(str(item).encode()).digest()
        a, b = int.from_bytes(d[:8], "big"), int.from_bytes(d[8:], "big") | 1
        return [(a + i * b) % self.m for i in range(self.k)]

    def add(self, item):
        for i in self._idx(item):
            self.bits[i] = True

    def remove(self, item):
        for i in self._idx(item):
            self.bits[i] = False

    def might_contain(self, item):
        return all(self.bits[i] for i in self._idx(item))
