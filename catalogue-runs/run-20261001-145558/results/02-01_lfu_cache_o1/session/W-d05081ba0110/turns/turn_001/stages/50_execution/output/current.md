class LFUCache:
    class Node:
        __slots__ = ('key', 'value', 'freq', 'prev', 'next')
        def __init__(self, key, value, freq=1):
            self.key = key
            self.value = value
            self.freq = freq
            self.prev = None
            self.next = None

    class DLinkedList:
        __slots__ = ('head', 'tail', 'size')
        def __init__(self):
            self.head = LFUCache.Node(None, None)  # dummy head
            self.tail = LFUCache.Node(None, None)  # dummy tail
            self.head.next = self.tail
            self.tail.prev = self.head
            self.size = 0
        def append(self, node):
            node.prev = self.tail.prev
            node.next = self.tail
            self.tail.prev.next = node
            self.tail.prev = node
            self.size += 1
        def pop(self, node=None):
            if self.size == 0:
                return None
            if node is None:
                node = self.head.next
            node.prev.next = node.next
            node.next.prev = node.prev
            self.size -= 1
            return node
        def is_empty(self):
            return self.size == 0

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.size = 0
        self.min_freq = 0
        self.key_node = {}               # key -> Node
        self.freq_list = {}              # freq -> DLinkedList

    def _update(self, node):
        freq = node.freq
        self.freq_list[freq].pop(node)
        if self.freq_list[freq].is_empty():
            del self.freq_list[freq]
            if self.min_freq == freq:
                self.min_freq += 1
        node.freq += 1
        self.freq_list.setdefault(node.freq, LFUCache.DLinkedList()).append(node)

    def get(self, key):
        if key not in self.key_node:
            return -1
        node = self.key_node[key]
        self._update(node)
        return node.value

    def put(self, key, value):
        if self.capacity == 0:
            return
        if key in self.key_node:
            node = self.key_node[key]
            node.value = value
            self._update(node)
            return
        if self.size == self.capacity:
            # evict LRU node from min_freq list
            lru_node = self.freq_list[self.min_freq].pop()
            del self.key_node[lru_node.key]
            self.size -= 1
        new_node = LFUCache.Node(key, value)
        self.key_node[key] = new_node
        self.freq_list.setdefault(1, LFUCache.DLinkedList()).append(new_node)
        self.min_freq = 1
        self.size += 1

# Test suite
import unittest

class TestLFUCache(unittest.TestCase):
    def test_capacity_and_eviction(self):
        cache = LFUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        self.assertEqual(cache.get(1), 1)  # freq of key 1 becomes 2
        cache.put(3, 3)  # evicts key 2 (freq 1)
        self.assertEqual(cache.get(2), -1)
        self.assertEqual(cache.get(3), 3)
        self.assertEqual(cache.get(1), 1)
        cache.put(4, 4)  # evicts key 3 (freq 1)
        self.assertEqual(cache.get(3), -1)
        self.assertEqual(cache.get(4), 4)

    def test_frequency_updates(self):
        cache = LFUCache(3)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.put(3, 3)
        cache.get(1)
        cache.get(1)
        cache.get(2)
        cache.put(4, 4)  # evicts key 3 (freq 1)
        self.assertEqual(cache.get(3), -1)
        self.assertEqual(cache.get(1), 1)
        self.assertEqual(cache.get(2), 2)
        self.assertEqual(cache.get(4), 4)

    def test_lru_tie_breaking(self):
        cache = LFUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.get(1)  # freq 1->2
        cache.put(3, 3)  # evicts key 2 (freq 1)
        self.assertEqual(cache.get(2), -1)
        self.assertEqual(cache.get(1), 1)
        self.assertEqual(cache.get(3), 3)
        # now both have freq 2, access order: 1 then 3
        cache.put(4, 4)  # evicts key 1 (LRU among freq 2)
        self.assertEqual(cache.get(1), -1)
        self.assertEqual(cache.get(3), 3)
        self.assertEqual(cache.get(4), 4)

if __name__ == '__main__':
    unittest.main()
