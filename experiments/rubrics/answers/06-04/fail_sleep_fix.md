The threads update `counter` concurrently, which can lose updates.

Fix (a): use a lock around the increment.
Fix (b): without a lock, add `time.sleep(0)` inside the loop so threads yield to each other and don't collide:

```python
def increment(n):
    global counter
    for _ in range(n):
        counter += 1
        time.sleep(0)
```

Both versions print Expected: 400000, Got: 400000.
