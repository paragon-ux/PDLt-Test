```python
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# Original implementation (for demonstration of deadlock risk)
lock_a = threading.Lock()
lock_b = threading.Lock()
results_original = []

def transfer_ab(amount):
    with lock_a:
        with lock_b:
            results_original.append(('ab', amount))

def transfer_ba(amount):
    # Inconsistent lock ordering: acquires lock_b then lock_a
    with lock_b:
        with lock_a:
            results_original.append(('ba', amount))

def test_deadlock_risk():
    """Run the original functions concurrently to illustrate the deadlock risk.
    The test starts many threads and joins with a timeout; if any thread hangs,
    the join will time out, indicating a deadlock scenario."""
    threads = []
    for i in range(50):
        t1 = threading.Thread(target=transfer_ab, args=(i,))
        t2 = threading.Thread(target=transfer_ba, args=(i,))
        threads.extend([t1, t2])
        t1.start()
        t2.start()
    # Join with timeout; if deadlock occurs, some threads will remain alive.
    for t in threads:
        t.join(timeout=2)
    # Detect hanging threads
    hanging = any(t.is_alive() for t in threads)
    assert hanging, "Expected a deadlock, but all threads completed"
    print("Deadlock risk demonstrated (some threads hung).")

# Fixed implementation with consistent lock ordering (lock_a then lock_b)
fixed_lock_a = threading.Lock()
fixed_lock_b = threading.Lock()
results_fixed = []

def transfer_ab_fixed(amount):
    # Acquire locks in global order: lock_a then lock_b
    with fixed_lock_a:
        with fixed_lock_b:
            results_fixed.append(('ab', amount))

def transfer_ba_fixed(amount):
    # Also acquire locks in global order: lock_a then lock_b
    with fixed_lock_a:
        with fixed_lock_b:
            results_fixed.append(('ba', amount))

def test_fixed_no_deadlock():
    """Run the fixed functions concurrently and verify they all finish.
    No thread should hang; the test will complete within the timeout."""
    threads = []
    for i in range(100):
        t1 = threading.Thread(target=transfer_ab_fixed, args=(i,))
        t2 = threading.Thread(target=transfer_ba_fixed, args=(i,))
        threads.extend([t1, t2])
        t1.start()
        t2.start()
    for t in threads:
        t.join(timeout=5)
    hanging = any(t.is_alive() for t in threads)
    assert not hanging, "Fixed code deadlocked unexpectedly"
    print("Fixed implementation completed without deadlock.")

if __name__ == "__main__":
    # Demonstrate deadlock risk (may or may not deadlock depending on timing)
    try:
        test_deadlock_risk()
    except AssertionError as e:
        print(e)
    # Verify the fixed version runs safely
    test_fixed_no_deadlock()
```
