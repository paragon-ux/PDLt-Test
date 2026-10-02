class LFUCache:
    class Node:
        __slots__ = ('key', 'value', 'freq', 'prev', 'next')
        def __init__(self, key, value):
            self.key = key
            self.value = value
            self.freq = 1
            self.prev = None
            self.next = None

    class DoublyLinkedList:
        __slots__ = ('head', 'tail')
        def __init__(self):
            self.head = self.tail = None
        def append(self, node):
            node.prev = node.next = None
            if not self.head:
                self.head = self.tail = node
            else:
                self.tail.next = node
                node.prev = self.tail
                self.tail = node
        def pop_left(self):
            if not self.head:
                return None
            node = self.head
            self.head = node.next
            if self.head:
                self.head.prev = None
            else:
                self.tail = None
            node.prev = node.next = None
            return node
        def remove(self, node):
            if node.prev:
                node.prev.next = node.next
            else:
                self.head = node.next
            if node.next:
                node.next.prev = node.prev
            else:
                self.tail = node.prev
            node.prev = node.next = None
        def is_empty(self):
            return self.head is None
        def __len__(self):
            cnt = 0
            cur = self.head
            while cur:
                cnt += 1
                cur = cur.next
            return cnt

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.size = 0
        self.min_freq = 0
        self.key_node = {}
        self.freq_list = {}

    def get(self, key: int) -> int:
        if key not in self.key_node:
            return -1
        node = self.key_node[key]
        self._update(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        if self.capacity == 0:
            return
        if key in self.key_node:
            node = self.key_node[key]
            node.value = value
            self._update(node)
        else:
            if self.size == self.capacity:
                self._evict()
            node = LFUCache.Node(key, value)
            self.key_node[key] = node
            self.freq_list.setdefault(1, LFUCache.DoublyLinkedList()).append(node)
            self.min_freq = 1
            self.size += 1

    def _update(self, node):
        freq = node.freq
        self.freq_list[freq].remove(node)
        if self.freq_list[freq].is_empty():
            del self.freq_list[freq]
            if self.min_freq == freq:
                self.min_freq += 1
        node.freq += 1
        self.freq_list.setdefault(node.freq, LFUCache.DoublyLinkedList()).append(node)

    def _evict(self):
        lru = self.freq_list[self.min_freq].pop_left()
        if self.freq_list[self.min_freq].is_empty():
            del self.freq_list[self.min_freq]
        del self.key_node[lru.key]
        self.size -= 1

# Self‑contained test suite
import unittest

class TestLFUCache(unittest.TestCase):
    def test_basic_operations(self):
        cache = LFUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        self.assertEqual(cache.get(1), 1)
        cache.put(3, 3)  # evicts key 2
        self.assertEqual(cache.get(2), -1)
        self.assertEqual(cache.get(3), 3)
        cache.put(4, 4)  # evicts key 1
        self.assertEqual(cache.get(1), -1)
        self.assertEqual(cache.get(3), 3)
        self.assertEqual(cache.get(4), 4)

    def test_frequency_updates(self):
        cache = LFUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.get(1)
        cache.get(1)
        cache.put(3, 3)  # evicts key 2 (freq 1) not key 1 (freq 3)
        self.assertEqual(cache.get(2), -1)
        self.assertEqual(cache.get(1), 1)
        self.assertEqual(cache.get(3), 3)

    def test_lru_tie_breaking(self):
        cache = LFUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.get(1)  # freq 2 for key1, freq1 for key2
        cache.get(2)  # both freq2 now, key1 is LRU
        cache.put(3, 3)  # evicts key1 (LRU among min freq)
        self.assertEqual(cache.get(1), -1)
        self.assertEqual(cache.get(2), 2)
        self.assertEqual(cache.get(3), 3)

if __name__ == '__main__':
    unittest.main()
