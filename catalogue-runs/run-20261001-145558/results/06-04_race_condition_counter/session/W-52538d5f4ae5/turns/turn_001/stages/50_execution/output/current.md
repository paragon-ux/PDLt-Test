```python
import threading
import time

# --- Original code (demonstrates race condition) ---
counter = 0

def increment(n):
    global counter
    for _ in range(n):
        counter += 1  # non‑atomic read‑modify‑write

threads = [threading.Thread(target=increment, args=(100000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print("[Race] Expected: 400000, Got:", counter)

# --- Fix (a): Use threading.Lock ---
counter_lock = 0
lock = threading.Lock()

def increment_locked(n):
    global counter_lock
    for _ in range(n):
        with lock:
            counter_lock += 1

threads = [threading.Thread(target=increment_locked, args=(100000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print("[Lock]   Expected: 400000, Got:", counter_lock)

# --- Fix (b): Use a thread‑safe data structure (queue) as a counter ---
from queue import SimpleQueue

q = SimpleQueue()

def producer(n):
    for _ in range(n):
        q.put(1)  # put is thread‑safe

threads = [threading.Thread(target=producer, args=(100000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
# drain the queue to count items
counter_q = 0
while not q.empty():
    q.get()
    counter_q += 1
print("[Queue]  Expected: 400000, Got:", counter_q)
```
