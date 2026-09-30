# Fix (a): Using threading.Lock
import threading

counter = 0
counter_lock = threading.Lock()

def increment_with_lock(n):
    global counter
    for _ in range(n):
        # protect the increment operation
        with counter_lock:
            counter += 1

threads = [threading.Thread(target=increment_with_lock, args=(100_000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Fix (a) - Expected: 400000, Got: {counter}")
assert counter == 400_000, "Counter mismatch in fix (a)"

# Fix (b): Using a thread‑safe atomic counter via multiprocessing.Value (shared memory)
import multiprocessing

# Note: multiprocessing.Value works with the 'fork' start method on Unix; on Windows we use a manager.
counter_val = multiprocessing.Value('i', 0)  # 'i' = signed int

def increment_atomic(n, shared_counter):
    for _ in range(n):
        with shared_counter.get_lock():
            shared_counter.value += 1

threads = [threading.Thread(target=increment_atomic, args=(100_000, counter_val)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Fix (b) - Expected: 400000, Got: {counter_val.value}")
assert counter_val.value == 400_000, "Counter mismatch in fix (b)"
