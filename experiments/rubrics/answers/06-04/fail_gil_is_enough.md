In CPython the GIL ensures that only one thread runs Python bytecode at a time, so `counter += 1` cannot actually be interrupted, and the program always prints 400000. The code is therefore correct in CPython; it would only be a problem in a free-threaded interpreter. For safety you can still add a lock:

```python
lock = threading.Lock()
def increment(n):
    global counter
    for _ in range(n):
        with lock:
            counter += 1
```
Without a lock, simply rely on the GIL.
