# Correct with a different interface: positional (n, p) named differently, and a
# murmur-style mixing function instead of a cryptographic hash.
import math


def _fmix(h):
    h ^= h >> 33
    h = (h * 0xFF51AFD7ED558CCD) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 33
    h = (h * 0xC4CEB9FE1A85EC53) & 0xFFFFFFFFFFFFFFFF
    return h ^ (h >> 33)


def _murmur_like(text, seed):
    h = seed
    for ch in text.encode():
        h = _fmix(h ^ ch)
    return h


class CBF:
    def __init__(self, n, p):
        self.size = int(math.ceil(-(n * math.log(p)) / math.log(2) ** 2))
        self.hashes = max(1, int(round(self.size / n * math.log(2))))
        self.cells = bytearray(self.size)

    def _slots(self, item):
        key = repr(item)
        return [_murmur_like(key, seed) % self.size for seed in range(1, self.hashes + 1)]

    def add(self, item):
        for s in self._slots(item):
            self.cells[s] = min(255, self.cells[s] + 1)

    def remove(self, item):
        slots = self._slots(item)
        if all(self.cells[s] for s in slots):
            for s in slots:
                self.cells[s] -= 1

    def might_contain(self, item):
        return all(self.cells[s] for s in self._slots(item))
