import threading
import time

class RingBuffer:
    """Single-producer single-consumer lock‑free ring buffer.
    Capacity must be a power of two; the mask is used for fast wrap‑around.
    """
    def __init__(self, capacity: int):
        if capacity & (capacity - 1) != 0:
            raise ValueError("capacity must be a power of 2")
        self.capacity = capacity
        self.mask = capacity - 1
        self.buffer = [None] * capacity
        # In CPython, simple integer stores/loads are atomic because of the GIL.
        self.head = 0  # index for consumer
        self.tail = 0  # index for producer

    def push(self, item) -> bool:
        """Attempt to enqueue *item*.
        Returns ``False`` if the buffer is full, ``True`` otherwise.
        """
        tail = self.tail
        head = self.head
        if (tail - head) & self.mask == self.mask:  # buffer full
            return False
        self.buffer[tail & self.mask] = item
        # advance tail atomically (GIL guarantees single‑threaded producer)
        self.tail = (tail + 1) & 0xFFFFFFFFFFFFFFFF
        return True

    def pop(self):
        """Attempt to dequeue an item.
        Returns ``None`` if the buffer is empty, otherwise the dequeued value.
        """
        head = self.head
        tail = self.tail
        if head == tail:  # buffer empty
            return None
        item = self.buffer[head & self.mask]
        # advance head atomically (GIL guarantees single‑threaded consumer)
        self.head = (head + 1) & 0xFFFFFFFFFFFFFFFF
        return item

# Test with two threads
N = 1 << 14  # 16384, power of two
rb = RingBuffer(N)
NUM_ITEMS = 100_000
produced = []  # not used, just for illustration
consumed = []

producer_done = threading.Event()

def producer():
    for i in range(NUM_ITEMS):
        while not rb.push(i):
            # busy‑wait until there is space
            time.sleep(0)  # yield
    producer_done.set()

def consumer():
    while len(consumed) < NUM_ITEMS:
        item = rb.pop()
        if item is not None:
            consumed.append(item)
        else:
            # buffer empty, wait a moment
            time.sleep(0)

prod_thread = threading.Thread(target=producer, name="producer")
cons_thread = threading.Thread(target=consumer, name="consumer")

prod_thread.start()
cons_thread.start()

prod_thread.join()
cons_thread.join()

# Verify order and completeness
assert len(consumed) == NUM_ITEMS, f"Expected {NUM_ITEMS} items, got {len(consumed)}"
assert consumed == list(range(NUM_ITEMS)), "Items out of order or missing"
print("Test passed: all items received in correct order.")
