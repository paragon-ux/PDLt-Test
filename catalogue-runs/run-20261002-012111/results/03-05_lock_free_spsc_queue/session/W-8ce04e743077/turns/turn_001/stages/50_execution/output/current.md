import threading
import time

class RingBuffer:
    """Lock‑free single‑producer single‑consumer (SPSC) ring buffer.
    The capacity N must be a power of two.
    """
    def __init__(self, capacity: int):
        if capacity <= 0 or (capacity & (capacity - 1)) != 0:
            raise ValueError("capacity must be a power of two and > 0")
        self.capacity = capacity
        self.mask = capacity - 1
        self.buffer = [None] * capacity
        self.head = 0  # producer index
        self.tail = 0  # consumer index
        # In CPython the GIL makes simple integer reads/writes atomic.

    def push(self, item) -> bool:
        """Attempt to push an item.
        Returns False if the buffer is full.
        """
        # Compute current distance without locking; safe for SPSC.
        if (self.head - self.tail) == self.capacity:
            return False  # full
        self.buffer[self.head & self.mask] = item
        # Increment head atomically (GIL guarantees atomicity for simple int)
        self.head += 1
        return True

    def pop(self):
        """Attempt to pop an item.
        Returns None if the buffer is empty.
        """
        if self.head == self.tail:
            return None  # empty
        item = self.buffer[self.tail & self.mask]
        self.tail += 1
        return item

# Multithreaded test
def test_ring_buffer():
    N = 1024  # power of two capacity
    rb = RingBuffer(N)
    total_items = 100_000
    produced = []
    consumed = []
    produce_done = threading.Event()

    def producer():
        for i in range(total_items):
            # spin until we can push
            while not rb.push(i):
                time.sleep(0)  # yield
        produce_done.set()

    def consumer():
        while not (produce_done.is_set() and rb.head == rb.tail):
            item = rb.pop()
            if item is not None:
                consumed.append(item)
            else:
                time.sleep(0)  # yield

    th_prod = threading.Thread(target=producer)
    th_cons = threading.Thread(target=consumer)
    th_prod.start()
    th_cons.start()
    th_prod.join()
    th_cons.join()

    assert len(consumed) == total_items, f"Expected {total_items} items, got {len(consumed)}"
    assert consumed == list(range(total_items)), "Items were out of order or duplicated"
    print("Test passed: all items received in order without duplicates or drops.")

if __name__ == "__main__":
    test_ring_buffer()
