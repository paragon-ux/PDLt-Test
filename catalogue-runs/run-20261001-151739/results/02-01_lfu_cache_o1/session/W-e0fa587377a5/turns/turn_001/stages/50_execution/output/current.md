class LFUCache:
    class Node:
        __slots__ = ('key', 'value', 'freq', 'prev', 'next')
        def __init__(self, key, value, freq=1):
            self.key = key
            self.value = value
            self.freq = freq
            self.prev = None
            self.next = None

    class DLList:
        __slots__ = ('head', 'tail')
        def __init__(self):
            self.head = LFUCache.Node(None, None)  # dummy head
            self.tail = LFUCache.Node(None, None)  # dummy tail
            self.head.next = self.tail
            self.tail.prev = self.head
        def append(self, node):
            node.prev = self.tail.prev
            node.next = self.tail
            self.tail.prev.next = node
            self.tail.prev = node
        def pop(self, node=None):
            if self.is_empty():
                return None
            if node is None:
                node = self.head.next
            node.prev.next = node.next
            node.next.prev = node.prev
            node.prev = node.next = None
            return node
        def is_empty(self):
            return self.head.next is self.tail

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.min_freq = 0
        self.key_node = {}
        self.freq_list = {}
        self.size = 0

    def get(self, key: int) -> int:
        if key not in self.key_node:
            return -1
        node = self.key_node[key]
        self._increase_freq(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        if self.capacity == 0:
            return
        if key in self.key_node:
            node = self.key_node[key]
            node.value = value
            self._increase_freq(node)
            return
        if self.size == self.capacity:
            self._evict()
        node = LFUCache.Node(key, value)
        self.key_node[key] = node
        self.freq_list.setdefault(1, LFUCache.DLList()).append(node)
        self.min_freq = 1
        self.size += 1

    def _increase_freq(self, node):
        freq = node.freq
        self.freq_list[freq].pop(node)
        if self.freq_list[freq].is_empty():
            del self.freq_list[freq]
            if self.min_freq == freq:
                self.min_freq += 1
        node.freq += 1
        self.freq_list.setdefault(node.freq, LFUCache.DLList()).append(node)

    def _evict(self):
        # evict LRU node from min_freq list
        lru_list = self.freq_list[self.min_freq]
        evicted = lru_list.pop()
        if lru_list.is_empty():
            del self.freq_list[self.min_freq]
        del self.key_node[evicted.key]
        self.size -= 1

# Self-contained test suite
import unittest

class TestLFUCache(unittest.TestCase):
    def test_basic_operations(self):
        cache = LFUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        self.assertEqual(cache.get(1), 1)   # freq of key1 becomes 2
        cache.put(3, 3)                    # evicts key2 (freq 1)
        self.assertEqual(cache.get(2), -1)
        self.assertEqual(cache.get(3), 3)
        self.assertEqual(cache.get(1), 1)   # freq of key1 becomes 3
        cache.put(4, 4)                    # evicts key3 (freq 1)
        self.assertEqual(cache.get(3), -1)
        self.assertEqual(cache.get(4), 4)

    def test_lru_tie_break(self):
        cache = LFUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        self.assertEqual(cache.get(1), 1)   # freq1=2, freq2=1
        cache.put(3, 3)                    # evicts key2 (freq1)
        self.assertEqual(cache.get(2), -1)
        self.assertEqual(cache.get(3), 3)
        # Both keys 1 and 3 have freq=1 now (after next get)
        cache.get(3)                       # freq3 becomes 2
        cache.put(4, 4)                    # evicts key1 (freq 1)
        self.assertEqual(cache.get(1), -1)
        self.assertEqual(cache.get(4), 4)

    def test_update_existing(self):
        cache = LFUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.put(1, 10)  # update value and increase freq
        self.assertEqual(cache.get(1), 10)
        cache.put(3, 3)  # evicts key2 (freq 1)
        self.assertEqual(cache.get(2), -1)
        self.assertEqual(cache.get(3), 3)

if __name__ == '__main__':
    unittest.main()
