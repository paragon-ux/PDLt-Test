import threading
import time

class SPSCQueue:
    """Lock‑free single‑producer single‑consumer ring buffer.
    Capacity N must be a power of two.
    """
    def __init__(self, capacity: int):
        if capacity <= 0 or (capacity & (capacity - 1)) != 0:
            raise ValueError("capacity must be a power of two and > 0")
        self._capacity = capacity
        self._mask = capacity - 1
        self._buffer = [None] * capacity
        self._head = 0  # producer index
        self._tail = 0  # consumer index

    def push(self, item) -> bool:
        """Enqueue *item*.
        Returns ``False`` if the buffer is full.
        """
        head = self._head  # atomic read (single thread)
        tail = self._tail  # atomic read (single thread)
        next_head = (head + 1) & self._mask
        if next_head == tail:
            return False  # full
        self._buffer[head] = item
        # atomic write
        self._head = next_head
        return True

    def pop(self):
        """Dequeue the next item.
        Returns ``None`` if the buffer is empty.
        """
        head = self._head  # atomic read
        tail = self._tail  # atomic read
        if head == tail:
            return None  # empty
        item = self._buffer[tail]
        self._buffer[tail] = None  # optional: help GC
        self._tail = (tail + 1) & self._mask
        return item

# Multithreaded test
def test_spsc_queue():
    N = 1 << 12  # 4096, a power of two
    q = SPSCQueue(N)
    count = 100_000
    produced = []
    consumed = []
    prod_done = threading.Event()

    def producer():
        for i in range(count):
            # busy‑wait until we can push
            while not q.push(i):
                pass
        prod_done.set()

    def consumer():
        while not (prod_done.is_set() and q.pop() is None):
            item = q.pop()
            if item is not None:
                consumed.append(item)
        # Drain any remaining items after producer finished
        while True:
            item = q.pop()
            if item is None:
                break
            consumed.append(item)

    t_prod = threading.Thread(target=producer)
    t_cons = threading.Thread(target=consumer)
    t_prod.start()
    t_cons.start()
    t_prod.join()
    t_cons.join()

    # Verify order and completeness
    assert len(consumed) == count, f"expected {count} items, got {len(consumed)}"
    assert consumed == list(range(count)), "items out of order or missing"
    print("Test passed: all items received in order.")

if __name__ == "__main__":
    test_spsc_queue()
