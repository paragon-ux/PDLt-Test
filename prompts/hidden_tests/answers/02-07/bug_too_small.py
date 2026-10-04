# Wrong: ignores the sizing formulas (m fixed at 1024, k = 2), so the false-positive
# rate is far above the target.
import hashlib


class CountingBloomFilter:
    def __init__(self, n, p):
        self.m, self.k = 1024, 2
        self.counts = [0] * self.m

    def _idx(self, item):
        d = hashlib.sha1(str(item).encode()).digest()
        return [int.from_bytes(d[i * 4:(i + 1) * 4], "big") % self.m for i in range(self.k)]

    def add(self, item):
        for i in self._idx(item):
            self.counts[i] += 1

    def remove(self, item):
        for i in self._idx(item):
            self.counts[i] = max(0, self.counts[i] - 1)

    def might_contain(self, item):
        return all(self.counts[i] for i in self._idx(item))
