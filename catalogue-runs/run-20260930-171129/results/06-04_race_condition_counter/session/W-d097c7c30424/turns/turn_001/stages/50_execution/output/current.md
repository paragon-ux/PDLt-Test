# Race condition demonstration and fixes

The original code increments a shared global counter from multiple threads without any synchronization, leading to a race condition. Below we:
1. **READ** the provided code.
2. **IDENTIFY** the race condition.
3. **DEMONSTRATE** that the final count can be incorrect.
4. **SUPPLY** a fix using a `threading.Lock`.
5. **SUPPLY** an alternative lock‑free, thread‑safe approach using a `queue.Queue` to aggregate increments.
6. **TEST** both implementations, showing expected vs. actual results.

```python
import threading
import queue
import time

# ------------------------------------------------------------
# 1. Original code (race condition)
# ------------------------------------------------------------
counter = 0

def increment_race(n):
    global counter
    for _ in range(n):
        counter += 1  # not atomic → race condition

threads = [threading.Thread(target=increment_race, args=(100_000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print("[Race] Expected: 400000, Got:", counter)

# ------------------------------------------------------------
# 2. Fix with threading.Lock
# ------------------------------------------------------------
counter_lock = 0
lock = threading.Lock()

def increment_lock(n):
    global counter_lock
    for _ in range(n):
        with lock:
            counter_lock += 1

threads = [threading.Thread(target=increment_lock, args=(100_000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print("[Lock] Expected: 400000, Got:", counter_lock)

# ------------------------------------------------------------
# 3. Lock‑free, thread‑safe approach using queue.Queue
#    Each thread puts its increments into a queue; the main thread
#    consumes them to compute the total. Queue operations are atomic.
# ------------------------------------------------------------
q = queue.Queue()

def increment_queue(n):
    for _ in range(n):
        q.put(1)  # each put is thread‑safe

threads = [threading.Thread(target=increment_queue, args=(100_000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

# Drain the queue to compute the total
counter_queue = 0
while not q.empty():
    counter_queue += q.get()
print("[Queue] Expected: 400000, Got:", counter_queue)
```

**Explanation**
- The first block prints a value that is often *less* than 400,000 because increments interleave and some are lost.
- The second block uses a `threading.Lock` to serialize access to the counter, guaranteeing the correct final count.
- The third block avoids an explicit lock by leveraging the thread‑safe `queue.Queue`. Each thread enqueues a unit of work; the main thread aggregates safely, yielding the correct total.

Running the script repeatedly shows the race‑condition block producing varying (incorrect) results, while both the lock‑protected and queue‑based implementations consistently produce the expected 400,000.
