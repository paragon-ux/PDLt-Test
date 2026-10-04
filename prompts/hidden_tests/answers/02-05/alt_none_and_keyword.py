# A correct LFU with a different interface: keyword capacity with a default,
# None for an absent key, and a helper class that the adapter must skip past.
import collections


class Node:
    def __init__(self, key, value):
        self.key, self.value, self.count = key, value, 1


class Cache:
    def __init__(self, max_size=128):
        self.max_size = max_size
        self.nodes = {}
        self.by_count = collections.defaultdict(collections.OrderedDict)
        self.lowest = 1

    def _bump(self, node):
        bucket = self.by_count[node.count]
        bucket.pop(node.key)
        if not bucket and self.lowest == node.count:
            self.lowest += 1
        node.count += 1
        self.by_count[node.count][node.key] = node

    def get(self, key):
        node = self.nodes.get(key)
        if node is None:
            return None
        self._bump(node)
        return node.value

    def put(self, key, value):
        node = self.nodes.get(key)
        if node is not None:
            node.value = value
            self._bump(node)
            return
        if len(self.nodes) >= self.max_size:
            while not self.by_count[self.lowest]:
                self.lowest += 1
            victim_key, _ = self.by_count[self.lowest].popitem(last=False)
            del self.nodes[victim_key]
        node = Node(key, value)
        self.nodes[key] = node
        self.by_count[1][key] = node
        self.lowest = 1


# An unguarded demo at module level: it must not disturb grading.
demo = Cache(2)
demo.put("a", 1)
print("demo", demo.get("a"))
