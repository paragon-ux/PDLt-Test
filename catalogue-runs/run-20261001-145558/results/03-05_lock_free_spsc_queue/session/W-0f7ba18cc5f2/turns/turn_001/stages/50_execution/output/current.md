import threading
import time

class SPSCQueue:
    def __init__(self, size):
        # size must be power of 2
        if size & (size - 1) != 0:
            raise ValueError('size must be power of 2')
        self.size = size
        self.mask = size - 1
        self.buffer = [None] * size
        self.head = 0  # producer index (write)
        self.tail = 0  # consumer index (read)
        # In CPython, simple integer reads/writes are atomic for the GIL.
        # The algorithm relies on a single producer and a single consumer.

    def push(self, item):
        head = self.head
        tail = self.tail
        next_head = (head + 1) & self.mask
        if next_head == tail:
            return False  # full
        self.buffer[head] = item
        # update head after storing
        self.head = next_head
        return True

    def pop(self):
        head = self.head
        tail = self.tail
        if tail == head:
            return None  # empty
        item = self.buffer[tail]
        self.buffer[tail] = None  # optional, help GC
        self.tail = (tail + 1) & self.mask
        return item

def test_spsc_queue():
    N = 1024  # power of two
    q = SPSCQueue(N)
    total_items = 100000
    pushed = []
    popped = []
    push_done = threading.Event()

    def producer():
        for i in range(1, total_items + 1):
            # busy-wait until we can push
            while not q.push(i):
                pass
        push_done.set()

    def consumer():
        while len(popped) < total_items:
            item = q.pop()
            if item is not None:
                popped.append(item)
            else:
                # if producer finished and queue empty, break
                if push_done.is_set():
                    break
        # ensure we have all items
        assert len(popped) == total_items

    t1 = threading.Thread(target=producer)
    t2 = threading.Thread(target=consumer)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    # Verify FIFO order
    assert popped == list(range(1, total_items + 1)), "FIFO order violated"
    print('Test passed')

if __name__ == '__main__':
    test_spsc_queue()
