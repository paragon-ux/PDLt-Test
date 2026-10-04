# Wrong: a leaf split drops the overflowing key, so keys go missing as the tree grows.
import bisect
import pickle


class BPlusTree:
    def __init__(self, order=4):
        self.order = order
        self.leaves = [([], [])]

    def _leaf_index(self, key):
        firsts = [ks[0] if ks else float("-inf") for ks, _ in self.leaves]
        return max(0, bisect.bisect_right(firsts, key) - 1)

    def insert(self, key, value):
        keys, values = self.leaves[self._leaf_index(key)]
        i = bisect.bisect_left(keys, key)
        keys.insert(i, key)
        values.insert(i, value)
        if len(keys) >= self.order:
            mid = len(keys) // 2
            right = (keys[mid + 1:], values[mid + 1:])  # bug: keys[mid] is lost
            del keys[mid:], values[mid:]
            self.leaves.insert(self._leaf_index(key) + 1, right)

    def search(self, key):
        keys, values = self.leaves[self._leaf_index(key)]
        i = bisect.bisect_left(keys, key)
        return values[i] if i < len(keys) and keys[i] == key else None

    def range_scan(self, lo, hi):
        return [(k, v) for ks, vs in self.leaves for k, v in zip(ks, vs) if lo <= k <= hi]

    def serialize(self):
        return pickle.dumps(self.leaves)

    @classmethod
    def deserialize(cls, data):
        tree = cls()
        tree.leaves = pickle.loads(data)
        return tree
