import math
import hashlib
import random
from collections import defaultdict

class CountingBloomFilter:
    def __init__(self, expected_elements: int, false_positive_rate: float):
        if expected_elements <= 0:
            raise ValueError("expected_elements must be positive")
        if not (0 < false_positive_rate < 1):
            raise ValueError("false_positive_rate must be between 0 and 1")
        self.n = expected_elements
        self.p = false_positive_rate
        # optimal size m = -(n * ln(p)) / (ln(2)^2)
        self.m = max(1, int(-self.n * math.log(self.p) / (math.log(2) ** 2)))
        # optimal k = (m/n) * ln(2)
        self.k = max(1, int(round((self.m / self.n) * math.log(2))))
        self.counters = [0] * self.m
        self.seed = random.randrange(1 << 30)

    def _hashes(self, item: bytes):
        # Generate k hash values using double hashing (Murmur3-like via hashlib.sha256)
        h1 = int(hashlib.sha256(item + b"0" + self.seed.to_bytes(4, 'little')).hexdigest(), 16)
        h2 = int(hashlib.sha256(item + b"1" + self.seed.to_bytes(4, 'little')).hexdigest(), 16)
        for i in range(self.k):
            yield (h1 + i * h2) % self.m

    def add(self, item):
        item_bytes = str(item).encode('utf-8')
        for pos in self._hashes(item_bytes):
            self.counters[pos] += 1

    def remove(self, item):
        item_bytes = str(item).encode('utf-8')
        for pos in self._hashes(item_bytes):
            if self.counters[pos] > 0:
                self.counters[pos] -= 1
            else:
                # Allow underflow gracefully (ignore)
                pass

    def might_contain(self, item) -> bool:
        item_bytes = str(item).encode('utf-8')
        return all(self.counters[pos] > 0 for pos in self._hashes(item_bytes))

def _test_counting_bloom_filter():
    n = 10000
    p = 0.01
    bf = CountingBloomFilter(expected_elements=n, false_positive_rate=p)
    # generate unique items
    items = [f"item_{i}_{random.random()}" for i in range(n)]
    for it in items:
        bf.add(it)
    # verify no false negatives
    false_negatives = sum(not bf.might_contain(it) for it in items)
    assert false_negatives == 0, f"False negatives detected: {false_negatives}"
    # test false positive rate
    non_items = [f"non_{i}_{random.random()}" for i in range(n)]
    false_positives = sum(bf.might_contain(it) for it in non_items)
    actual_fpr = false_positives / n
    # theoretical bound
    theoretical_fpr = (1 - math.exp(-bf.k * n / bf.m)) ** bf.k
    assert actual_fpr <= 2 * theoretical_fpr, (
        f"Actual FPR {actual_fpr:.4f} exceeds 2x theoretical {theoretical_fpr:.4f}"
    )
    print("Test passed. Actual FPR:", actual_fpr, "Theoretical FPR:", theoretical_fpr)

if __name__ == "__main__":
    _test_counting_bloom_filter()
