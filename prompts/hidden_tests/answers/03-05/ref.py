class SPSCQueue:
    """Head is written only by the consumer, tail only by the producer."""

    def __init__(self, capacity):
        if capacity <= 0 or capacity & (capacity - 1):
            raise ValueError("capacity must be a power of 2")
        self._buf = [None] * capacity
        self._mask = capacity - 1
        self._head = 0  # next slot to read
        self._tail = 0  # next slot to write

    def push(self, item):
        tail = self._tail
        if tail - self._head == len(self._buf):
            return False
        self._buf[tail & self._mask] = item
        self._tail = tail + 1  # publish after the slot is written
        return True

    def pop(self):
        head = self._head
        if head == self._tail:
            return None
        item = self._buf[head & self._mask]
        self._buf[head & self._mask] = None
        self._head = head + 1
        return item
