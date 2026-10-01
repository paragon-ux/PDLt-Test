The following code has a race condition. Identify it, prove the bug can produce incorrect results, and fix it using proper synchronization.

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

Provide two fixes: (a) using a threading.Lock, and (b) using no explicit lock (hint: consider a thread-safe data structure or atomic-like approach in Python). Test both.
