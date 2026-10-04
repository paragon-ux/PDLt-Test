# Correct with a different interface: range_query returns a dict.
import random


class OrderedMap:
    class Node:
        def __init__(self, key=None, value=None, height=1):
            self.key, self.value, self.next = key, value, [None] * height

    def __init__(self, max_level=16):
        self.max_level = max_level
        self.head = self.Node(height=max_level)

    def _level(self):
        h = 1
        while h < self.max_level and random.random() < 0.5:
            h += 1
        return h

    def insert(self, key, value):
        prev, node = [None] * self.max_level, self.head
        for i in reversed(range(self.max_level)):
            while node.next[i] and node.next[i].key < key:
                node = node.next[i]
            prev[i] = node
        if node.next[0] and node.next[0].key == key:
            node.next[0].value = value
            return
        new = self.Node(key, value, self._level())
        for i in range(len(new.next)):
            new.next[i], prev[i].next[i] = prev[i].next[i], new

    def search(self, key):
        node = self.head
        for i in reversed(range(self.max_level)):
            while node.next[i] and node.next[i].key < key:
                node = node.next[i]
        node = node.next[0]
        return node.value if node and node.key == key else None

    def delete(self, key):
        node = self.head
        for i in reversed(range(self.max_level)):
            while node.next[i] and node.next[i].key < key:
                node = node.next[i]
            if node.next[i] and node.next[i].key == key:
                node.next[i] = node.next[i].next[i]

    def range_query(self, lo, hi):
        node, found = self.head.next[0], {}
        while node and node.key <= hi:
            if node.key >= lo:
                found[node.key] = node.value
            node = node.next[0]
        return found
