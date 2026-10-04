# Wrong: correct search and range scan, but no serialization, which the prompt requires.
import bisect


class BPlusTree:
    def __init__(self, order=4):
        self.keys, self.values = [], []

    def insert(self, key, value):
        i = bisect.bisect_left(self.keys, key)
        if i < len(self.keys) and self.keys[i] == key:
            self.values[i] = value
        else:
            self.keys.insert(i, key)
            self.values.insert(i, value)

    def search(self, key):
        i = bisect.bisect_left(self.keys, key)
        return self.values[i] if i < len(self.keys) and self.keys[i] == key else None

    def range_scan(self, lo, hi):
        return [(k, v) for k, v in zip(self.keys, self.values) if lo <= k <= hi]
