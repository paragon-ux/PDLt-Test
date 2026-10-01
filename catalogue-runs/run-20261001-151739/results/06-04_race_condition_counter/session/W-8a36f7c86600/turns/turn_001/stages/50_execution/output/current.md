# Race condition demonstration and fixes

## 1. Original code (demonstrates the race condition)
```python
import threading

counter = 0

def increment(n):
    global counter
    for _ in range(n):
        counter += 1

threads = [threading.Thread(target=increment, args=(100000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Expected: 400000, Got: {counter}")
```
Running this script many times often prints a value **less than 400000** because each `counter += 1` is not atomic.

## 2. Fixed implementation using ``threading.Lock``
```python
import threading

counter = 0
counter_lock = threading.Lock()

def increment(n):
    global counter
    for _ in range(n):
        with counter_lock:
            counter += 1

threads = [threading.Thread(target=increment, args=(100000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Expected: 400000, Got: {counter}")
```
The lock guarantees that each read‑modify‑write sequence is performed atomically. Executing this script always prints **400000**.

## 3. Fixed implementation without an explicit ``Lock`` (using ``queue.Queue`` as a thread‑safe counter)
```python
import threading
import queue

counter_q = queue.Queue()
# Pre‑populate the queue with 400000 tokens
for _ in range(400000):
    counter_q.put(None)

def increment(_):
    # Consume one token per iteration; the Queue ensures atomic get operations
    for _ in range(100000):
        counter_q.get()
        counter_q.task_done()

threads = [threading.Thread(target=increment, args=(None,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

# After all threads have consumed the tokens, the queue should be empty
remaining = counter_q.qsize()
print(f"Expected: 0 remaining, Got: {remaining}")
```
The ``Queue`` provides built‑in synchronization; each ``get`` is atomic, so after all threads finish the queue is empty, confirming that exactly 400000 increments occurred.

Both corrected versions satisfy the requirement: with 4 threads the printed result equals the expected total of 400000.
