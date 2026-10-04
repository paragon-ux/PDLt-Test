**The race.** `counter += 1` is three steps: read `counter`, add 1, write it back. If thread A reads 10, then thread B reads 10 and writes 11, A then writes 11 as well: one increment is lost. The GIL serializes bytecodes, not this three-step sequence, so a thread switch between the load and the store loses updates. It is rare in CPython (the switch interval is 5 ms) but possible, and it becomes frequent with `sys.setswitchinterval(1e-6)`:

```python
import sys, threading
sys.setswitchinterval(1e-6)
counter = 0
def increment(n):
    global counter
    for _ in range(n):
        counter += 1
ts = [threading.Thread(target=increment, args=(100000,)) for _ in range(4)]
[t.start() for t in ts]; [t.join() for t in ts]
print(counter)  # typically < 400000
```

**Fix (a): a lock.**
```python
lock = threading.Lock()
def increment_locked(n):
    global counter
    for _ in range(n):
        with lock:
            counter += 1
```

**Fix (b): no explicit lock.** Each thread counts privately; the totals are combined after join.
```python
def run_partial(n_threads=4, n=100000):
    partial = [0] * n_threads
    def work(i):
        local = 0
        for _ in range(n):
            local += 1
        partial[i] = local          # each thread writes only its own slot
    ts = [threading.Thread(target=work, args=(i,)) for i in range(n_threads)]
    [t.start() for t in ts]; [t.join() for t in ts]
    return sum(partial)
```

**Tests.**
```python
def test_locked():
    global counter
    counter = 0
    ts = [threading.Thread(target=increment_locked, args=(100000,)) for _ in range(4)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert counter == 400000

def test_partial():
    assert run_partial() == 400000
```
