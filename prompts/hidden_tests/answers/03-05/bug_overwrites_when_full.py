# Wrong: never reports full; the producer overwrites unread slots.
class SPSCQueue:
    def __init__(self, capacity):
        self._buf = [None] * capacity
        self._mask = capacity - 1
        self._head = 0
        self._tail = 0

    def push(self, item):
        self._buf[self._tail & self._mask] = item
        self._tail += 1
        return True

    def pop(self):
        if self._head == self._tail:
            return None
        item = self._buf[self._head & self._mask]
        self._head += 1
        return item
