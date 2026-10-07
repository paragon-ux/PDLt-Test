# Correct with a different interface: the original is kept for the demonstration,
# and the fix acquires the second lock with a timeout, backing off on failure.
import random
import threading
import time

lock_a = threading.Lock()
lock_b = threading.Lock()
results = []


def transfer_ab_original(amount):
    with lock_a:
        with lock_b:
            results.append(('ab', amount))


def transfer_ba_original(amount):
    with lock_b:
        with lock_a:
            results.append(('ba', amount))


def _both(first, second, record):
    while True:
        with first:
            if second.acquire(timeout=0.05):
                try:
                    results.append(record)
                    return
                finally:
                    second.release()
        time.sleep(random.random() * 0.01)


def transfer_ab_fixed(amount):
    _both(lock_a, lock_b, ('ab', amount))


def transfer_ba_fixed(amount):
    _both(lock_b, lock_a, ('ba', amount))
