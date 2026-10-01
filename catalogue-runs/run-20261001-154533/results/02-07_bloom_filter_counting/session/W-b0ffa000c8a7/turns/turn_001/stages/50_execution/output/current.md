import math
import hashlib
from array import array

class CountingBloomFilter:
    def __init__(self, n, p):
        """Initialize a counting Bloom filter.
        n: expected number of elements
        p: desired false positive probability
        """
        self.n = n
        self.p = p
        # optimal size m = -(n * ln(p)) / (ln(2)^2)
        self.m = int(-n * math.log(p) / (math.log(2) ** 2))
        # optimal number of hash functions k = (m / n) * ln(2)
        self.k = max(1, int(round((self.m / n) * math.log(2))))
        self.counts = array('I', (0 for _ in range(self.m)))
        self.seeds = [i for i in range(self.k)]

    def _hashes(self, item):
        data = str(item).encode('utf-8')
        for seed in self.seeds:
            h = hashlib.blake2b(data, digest_size=8, person=seed.to_bytes(8, 'little')).digest()
            # convert to integer and modulo m
            yield int.from_bytes(h, 'little') % self.m

    def add(self, item):
        for idx in self._hashes(item):
            self.counts[idx] += 1

    def remove(self, item):
        for idx in self._hashes(item):
            if self.counts[idx] > 0:
                self.counts[idx] -= 1

    def might_contain(self, item):
        return all(self.counts[idx] > 0 for idx in self._hashes(item))

# Test harness
if __name__ == "__main__":
    n_expected = 10000
    false_pos_target = 0.01  # 1% target
    bf = CountingBloomFilter(n_expected, false_pos_target)
    # Insert items
    items = [f"item_{i}" for i in range(n_expected)]
    for it in items:
        bf.add(it)
    # Verify no false negatives
    false_negatives = sum(1 for it in items if not bf.might_contain(it))
    print(f"False negatives: {false_negatives}")
    # Test false positive rate
    test_queries = [f"query_{i}" for i in range(n_expected)]
    false_positives = sum(1 for q in test_queries if bf.might_contain(q))
    observed_fp_rate = false_positives / n_expected
    theoretical_fp = (1 - math.exp(-bf.k * n_expected / bf.m)) ** bf.k
    print(f"Observed FP rate: {observed_fp_rate:.4f}")
    print(f"Theoretical FP rate: {theoretical_fp:.4f}")
    print(f"Within 2x bound: {observed_fp_rate <= 2 * theoretical_fp}")
