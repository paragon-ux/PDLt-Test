# Correct with a different interface: RingBuffer(size=...), indices kept modulo the
# capacity with one slot left empty (holds size - 1 items), push returns None on
# success.
class RingBuffer:
    def __init__(self, size=16):
        self.size = size
        self.slots = [None] * size
        self.read_idx = 0
        self.write_idx = 0

    def push(self, item):
        nxt = (self.write_idx + 1) & (self.size - 1)
        if nxt == self.read_idx:
            return False
        self.slots[self.write_idx] = item
        self.write_idx = nxt

    def pop(self):
        if self.read_idx == self.write_idx:
            return None
        item = self.slots[self.read_idx]
        self.read_idx = (self.read_idx + 1) & (self.size - 1)
        return item
