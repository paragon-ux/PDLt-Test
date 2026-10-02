import math
import hashlib
import struct
from typing import Any

class CountingBloomFilter:
    """Counting Bloom filter with configurable false positive rate.

    Parameters
    ----------
    n : int
        Expected number of distinct elements to be stored.
    p : float
        Desired false positive probability (0 < p < 1).
    """
    def __init__(self, n: int, p: float):
        if n <= 0:
            raise ValueError("Expected element count n must be positive")
        if not (0 < p < 1):
            raise ValueError("False positive rate p must be in (0,1)")
        # optimal size m and number of hash functions k
        self.m = int(- (n * math.log(p)) / (math.log(2) ** 2))
        self.k = max(1, int(round((self.m / n) * math.log(2))))
        self.counts = [0] * self.m
        # generate k distinct seeds for murmur-style hashing
        self.seeds = [i for i in range(self.k)]

    def _hashes(self, item: Any):
        """Generate k hash values for *item* using murmur-style hashing.
        The item is first converted to UTF‑8 bytes.
        """
        data = str(item).encode('utf-8')
        for seed in self.seeds:
            # hashlib.blake2b can be used as a stand‑in for murmur hash
            h = hashlib.blake2b(data, digest_size=8, person=struct.pack('>Q', seed))
            # Produce a 64‑bit integer
            yield int.from_bytes(h.digest(), 'big') % self.m

    def add(self, item: Any) -> None:
        for idx in self._hashes(item):
            self.counts[idx] += 1

    def remove(self, item: Any) -> None:
        for idx in self._hashes(item):
            if self.counts[idx] > 0:
                self.counts[idx] -= 1

    def might_contain(self, item: Any) -> bool:
        return all(self.counts[idx] > 0 for idx in self._hashes(item))

# Test suite
if __name__ == "__main__":
    import random
    random.seed(0)
    n_expected = 10000
    false_positive_target = 0.01  # 1%
    bf = CountingBloomFilter(n_expected, false_positive_target)
    # Insert 10,000 distinct items
    inserted = [f"item_{i}" for i in range(n_expected)]
    for it in inserted:
        bf.add(it)
    # Verify zero false negatives
    false_negatives = sum(1 for it in inserted if not bf.might_contain(it))
    print(f"False negatives: {false_negatives}")
    # Query 10,000 non‑member items
    non_members = [f"non_{i}" for i in range(n_expected)]
    false_positives = sum(1 for it in non_members if bf.might_contain(it))
    observed_fpr = false_positives / n_expected
    theoretical_fpr = (1 - math.exp(-bf.k * n_expected / bf.m)) ** bf.k
    print(f"Observed false positive rate: {observed_fpr:.4f}")
    print(f"Theoretical false positive rate: {theoretical_fpr:.4f}")
    # Check within 2x bound
    within_bound = observed_fpr <= 2 * theoretical_fpr
    print(f"Within 2x bound: {within_bound}")
