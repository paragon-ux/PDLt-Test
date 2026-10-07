# Wrong: avoids the hang by giving up when the second lock is busy, silently
# dropping the transfer.
import threading

lock_a = threading.Lock()
lock_b = threading.Lock()
results = []


def transfer_ab(amount):
    with lock_a:
        if lock_b.acquire(timeout=0.01):
            try:
                results.append(('ab', amount))
            finally:
                lock_b.release()


def transfer_ba(amount):
    with lock_b:
        if lock_a.acquire(timeout=0.01):
            try:
                results.append(('ba', amount))
            finally:
                lock_a.release()
