```python
import threading
import time

# Shared resources
lock_a = threading.Lock()
lock_b = threading.Lock()
results = []

# Consistent lock ordering: always acquire lock_a then lock_b
def transfer_ab(amount):
    with lock_a:
        with lock_b:
            results.append(('ab', amount))

def transfer_ba(amount):
    # Acquire locks in the same order as transfer_ab
    with lock_a:
        with lock_b:
            results.append(('ba', amount))

def run_test(deadlock_demo=True):
    threads = []
    for i in range(100):
        if deadlock_demo:
            # Original functions that could deadlock
            threads.append(threading.Thread(target=transfer_ab_original, args=(i,)))
            threads.append(threading.Thread(target=transfer_ba_original, args=(i,)))
        else:
            # Fixed functions with consistent lock ordering
            threads.append(threading.Thread(target=transfer_ab, args=(i,)))
            threads.append(threading.Thread(target=transfer_ba, args=(i,)))
    for t in threads:
        t.start()
    start = time.time()
    for t in threads:
        t.join(timeout=5)
    elapsed = time.time() - start
    return elapsed, any(t.is_alive() for t in threads)

# Original (deadlocking) implementations for demonstration

def transfer_ab_original(amount):
    with lock_a:
        with lock_b:
            results.append(('ab', amount))

def transfer_ba_original(amount):
    with lock_b:
        with lock_a:
            results.append(('ba', amount))

if __name__ == "__main__":
    # Demonstrate deadlock risk
    elapsed_dead, still_running_dead = run_test(deadlock_demo=True)
    print(f"Original run: elapsed={elapsed_dead:.2f}s, any thread still alive={still_running_dead}")
    # Verify corrected version does not hang
    elapsed_fixed, still_running_fixed = run_test(deadlock_demo=False)
    print(f"Fixed run: elapsed={elapsed_fixed:.2f}s, any thread still alive={still_running_fixed}")
```
