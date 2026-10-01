import math
import hashlib
import random
from collections import defaultdict

class CountingBloomFilter:
    """Counting Bloom filter with configurable false positive rate.
    
    Parameters
    ----------
    n : int
        Expected number of elements to be stored.
    p : float
        Desired false positive probability (e.g., 0.01 for 1%).
    """
    def __init__(self, n: int, p: float):
        if n <= 0:
            raise ValueError("Expected element count n must be positive")
        if not (0 < p < 1):
            raise ValueError("False positive rate p must be in (0,1)")
        # Optimal size (bits) for a standard Bloom filter
        m_float = -(n * math.log(p)) / (math.log(2) ** 2)
        self.m = int(math.ceil(m_float))  # number of counters
        # Number of hash functions
        k_float = (self.m / n) * math.log(2)
        self.k = max(1, int(round(k_float)))
        # Use an array of 8‑bit counters (could be larger if needed)
        self.counters = [0] * self.m
        # Seed for hash diversification
        self._seed = random.getrandbits(64)

    def _hashes(self, item: bytes):
        """Generate k independent hash values in range [0, m).
        
        Uses double‑hashing technique with MurmurHash‑like behavior via hashlib.sha256.
        """
        # First hash
        h1 = int(hashlib.sha256(item + self._seed.to_bytes(8, "little")).hexdigest(), 16)
        # Second hash with a different constant
        h2 = int(hashlib.sha256(item + (self._seed ^ 0xFFFFFFFFFFFFFFFF).to_bytes(8, "little")).hexdigest(), 16)
        for i in range(self.k):
            # (h1 + i * h2) mod m gives k distinct indices
            yield (h1 + i * h2) % self.m

    def add(self, item):
        """Increment counters for the item."""
        data = str(item).encode('utf-8')
        for idx in self._hashes(data):
            self.counters[idx] += 1

    def remove(self, item):
        """Decrement counters for the item, never below zero."""
        data = str(item).encode('utf-8')
        for idx in self._hashes(data):
            if self.counters[idx] > 0:
                self.counters[idx] -= 1

    def might_contain(self, item) -> bool:
        """Return True if all counters are > 0, else False."""
        data = str(item).encode('utf-8')
        return all(self.counters[idx] > 0 for idx in self._hashes(data))

# -------------------- Test --------------------
if __name__ == "__main__":
    import time
    n_expected = 10000
    false_positive_target = 0.01  # 1%
    bf = CountingBloomFilter(n_expected, false_positive_target)
    print(f"Filter size m={bf.m}, k={bf.k}, target p={false_positive_target}")
    # Generate distinct items
    inserts = [f"item-{i}" for i in range(n_expected)]
    for item in inserts:
        bf.add(item)
    # Verify zero false negatives
    false_negatives = sum(1 for item in inserts if not bf.might_contain(item))
    print(f"False negatives: {false_negatives}")
    assert false_negatives == 0, "There are false negatives!"
    # Generate non‑member queries
    non_members = [f"nonmember-{i}" for i in range(n_expected)]
    false_positives = sum(1 for item in non_members if bf.might_contain(item))
    measured_fp_rate = false_positives / n_expected
    # Theoretical false positive probability for counting Bloom filter equals standard BF
    theoretical_fp = (1 - math.exp(-bf.k * n_expected / bf.m)) ** bf.k
    print(f"Measured false positive rate: {measured_fp_rate:.4f}")
    print(f"Theoretical false positive rate: {theoretical_fp:.4f}")
    assert measured_fp_rate <= 2 * theoretical_fp, "Measured false positive rate exceeds 2× theoretical bound"
    print("Test passed: measured false positive rate within acceptable bounds.")
