# Race condition demonstration and two fixes
# Original race condition (may produce incorrect result)
import threading

counter = 0

def increment(n):
    global counter
    for _ in range(n):
        counter += 1

def run_original():
    global counter
    counter = 0
    threads = [threading.Thread(target=increment, args=(100000,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"Original -> Expected: 400000, Got: {counter}")

# Fix A: using threading.Lock
import threading

counter_a = 0
lock = threading.Lock()

def increment_locked(n):
    global counter_a
    for _ in range(n):
        with lock:
            counter_a += 1

def run_fixed_lock():
    global counter_a
    counter_a = 0
    threads = [threading.Thread(target=increment_locked, args=(100000,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"Fix A (Lock) -> Expected: 400000, Got: {counter_a}")

# Fix B: using thread‑safe queue as atomic counter
import queue

counter_b = queue.Queue()
# preload with zeros
for _ in range(400000):
    counter_b.put(0)

def increment_queue(n):
    for _ in range(n):
        # get and put back incremented value atomically
        val = counter_b.get()
        counter_b.put(val + 1)

def run_fixed_queue():
    # reset queue
    while not counter_b.empty():
        counter_b.get()
    for _ in range(400000):
        counter_b.put(0)
    threads = [threading.Thread(target=increment_queue, args=(100000,)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # sum all items
    total = 0
    while not counter_b.empty():
        total += counter_b.get()
    print(f"Fix B (Queue) -> Expected: 400000, Got: {total}")

if __name__ == "__main__":
    run_original()
    run_fixed_lock()
    run_fixed_queue()
