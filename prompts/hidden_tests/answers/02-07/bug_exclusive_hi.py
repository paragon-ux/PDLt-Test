# Wrong: range_query excludes hi, and update inserts a duplicate key.
import bisect


class SkipList:
    def __init__(self):
        self.keys, self.values = [], []

    def insert(self, key, value):
        i = bisect.bisect_left(self.keys, key)
        self.keys.insert(i, key)
        self.values.insert(i, value)

    def search(self, key):
        i = bisect.bisect_left(self.keys, key)
        return self.values[i] if i < len(self.keys) and self.keys[i] == key else None

    def delete(self, key):
        i = bisect.bisect_left(self.keys, key)
        if i < len(self.keys) and self.keys[i] == key:
            del self.keys[i], self.values[i]

    def range_query(self, lo, hi):
        i, j = bisect.bisect_left(self.keys, lo), bisect.bisect_left(self.keys, hi)
        return list(zip(self.keys[i:j], self.values[i:j]))
