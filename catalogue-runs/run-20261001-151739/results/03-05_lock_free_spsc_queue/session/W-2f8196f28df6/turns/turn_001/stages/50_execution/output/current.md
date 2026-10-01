# spsc_ring_buffer.py
# Single‑Producer Single‑Consumer lock‑free ring buffer implementation in pure Python.
# Capacity N must be a power of two.
# push(item) returns False if the buffer is full.
# pop() returns None if the buffer is empty.
# The implementation relies on the atomicity guarantees of the Python GIL for simple
# integer reads/writes – no explicit locks or mutexes are used.

import threading
import time

class SPSCQueue:
    def __init__(self, capacity: int):
        if capacity <= 0 or (capacity & (capacity - 1)) != 0:
            raise ValueError("capacity must be a power of two and > 0")
        self._mask = capacity - 1
        self._buffer = [None] * capacity
        self._head = 0  # consumer index
        self._tail = 0  # producer index

    def push(self, item) -> bool:
        tail = self._tail
        next_tail = (tail + 1) & self._mask
        # read head after computing next_tail to avoid stale read race
        head = self._head
        if next_tail == head:
            # buffer full
            return False
        self._buffer[tail] = item
        # write tail after storing the item
        self._tail = next_tail
        return True

    def pop(self):
        head = self._head
        tail = self._tail
        if head == tail:
            # buffer empty
            return None
        item = self._buffer[head]
        # optional: clear slot for GC purposes (not required for correctness)
        self._buffer[head] = None
        self._head = (head + 1) & self._mask
        return item

# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import threading

    N = 1024  # power‑of‑2 capacity
    TOTAL = 100_000
    q = SPSCQueue(N)

    produced = []  # for sanity check – not used by consumer
    consumed = []
    prod_done = threading.Event()

    def producer():
        for i in range(TOTAL):
            # spin until we can push
            while not q.push(i):
                # busy‑wait; in real code you might yield
                pass
            produced.append(i)
        prod_done.set()

    def consumer():
        while len(consumed) < TOTAL:
            item = q.pop()
            if item is None:
                # buffer empty – wait a bit
                continue
            consumed.append(item)
        # ensure producer has finished
        prod_done.wait()

    t_prod = threading.Thread(target=producer)
    t_cons = threading.Thread(target=consumer)
    t_prod.start()
    t_cons.start()
    t_prod.join()
    t_cons.join()

    # Verification
    assert len(consumed) == TOTAL, f"expected {TOTAL} items, got {len(consumed)}"
    assert consumed == list(range(TOTAL)), "items not received in order or missing"
    print("Test passed: all items received in order with no duplicates or drops.")
