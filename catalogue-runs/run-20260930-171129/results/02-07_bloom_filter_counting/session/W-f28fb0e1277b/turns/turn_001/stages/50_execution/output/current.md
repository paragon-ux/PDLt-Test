import math
import hashlib
from array import array

class CountingBloomFilter:
    """Counting Bloom filter with automatically computed size and hash count.
    Uses murmurstyle hash via hashlib.blake2b with different seeds.
    """
    def __init__(self, n: int, p: float):
        if n <= 0:
            raise ValueError("expected element count n must be positive")
        if not (0 < p < 1):
            raise ValueError("false positive rate p must be between 0 and 1")
        # optimal size m = -n * ln(p) / (ln 2)^2
        self.m = math.ceil(-n * math.log(p) / (math.log(2) ** 2))
        # optimal number of hash functions k = (m/n) * ln 2
        self.k = max(1, round((self.m / n) * math.log(2)))
        # use byte array for counters, each counter fits in unsigned short
        self.counts = array('H', (0 for _ in range(self.m)))
        self.n = n
        self.p = p

    def _hashes(self, item: bytes):
        # generate k hashes using blake2b with different salts
        for i in range(self.k):
            h = hashlib.blake2b(item, digest_size=8, person=bytes([i]))
            # convert to integer and modulo m
            yield int.from_bytes(h.digest(), 'little') % self.m

    def add(self, item):
        b = str(item).encode('utf-8')
        for idx in self._hashes(b):
            if self.counts[idx] < 65535:
                self.counts[idx] += 1

    def remove(self, item):
        b = str(item).encode('utf-8')
        for idx in self._hashes(b):
            if self.counts[idx] > 0:
                self.counts[idx] -= 1

    def might_contain(self, item) -> bool:
        b = str(item).encode('utf-8')
        return all(self.counts[idx] > 0 for idx in self._hashes(b))

# Test harness
if __name__ == "__main__":
    n = 10000
    p = 0.01
    filter = CountingBloomFilter(n, p)
    # Insert distinct items
    inserted = [f"item{i}" for i in range(n)]
    for itm in inserted:
        filter.add(itm)
    # Verify zero false negatives
    false_negatives = sum(1 for itm in inserted if not filter.might_contain(itm))
    assert false_negatives == 0, f"False negatives detected: {false_negatives}"
    # Query non‑member items
    test_non_members = [f"other{i}" for i in range(n, 2*n)]
    false_positives = sum(1 for itm in test_non_members if filter.might_contain(itm))
    observed_fp_rate = false_positives / n
    # Theoretical bound for counting Bloom filter is same as standard Bloom
    m = filter.m
    k = filter.k
    theoretical_fp = (1 - math.exp(-k * n / m)) ** k
    assert observed_fp_rate <= 2 * theoretical_fp, (
        f"Observed FP rate {observed_fp_rate:.4f} exceeds twice the theoretical {theoretical_fp:.4f}"
    )
    print(f"Observed false positive rate: {observed_fp_rate:.4f}, theoretical bound: {theoretical_fp:.4f}")
