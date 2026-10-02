import threading

# ---------- Version 1: Using threading.Lock ----------
counter_lock = 0
lock = threading.Lock()

def increment_lock(n):
    global counter_lock
    for _ in range(n):
        with lock:
            counter_lock += 1

def test_lock():
    threads = [threading.Thread(target=increment_lock, args=(100000,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"Lock version - Expected: 400000, Got: {counter_lock}")

# ---------- Version 2: Using thread‑safe atomic-like counter ----------
# Python's standard library lacks a true lock‑free atomic integer, but we can use
# a mutable object from the `queue` module that provides internal locking, or a
# `collections.Counter` protected by the GIL for simple increments. Here we use
# `queue.SimpleQueue` as a holder for the integer and update it via `put`/`get`
# which are atomic.
from queue import SimpleQueue
counter_atomic = SimpleQueue()
# initialise with 0
counter_atomic.put(0)

def increment_atomic(n):
    for _ in range(n):
        # get the current value, increment, and put back – the get/put pair is
        # atomic because SimpleQueue operations are thread‑safe.
        val = counter_atomic.get()
        counter_atomic.put(val + 1)

def test_atomic():
    # reset counter to 0
    while not counter_atomic.empty():
        counter_atomic.get()
    counter_atomic.put(0)
    threads = [threading.Thread(target=increment_atomic, args=(100000,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    final = counter_atomic.get()
    print(f"Atomic version - Expected: 400000, Got: {final}")

if __name__ == "__main__":
    print("Running lock‑based test:")
    test_lock()
    print("Running lock‑free test:")
    test_atomic()
