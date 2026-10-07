# Wrong: the original lock-order inversion, unchanged.
import threading

lock_a = threading.Lock()
lock_b = threading.Lock()
results = []


def transfer_ab(amount):
    with lock_a:
        with lock_b:
            results.append(('ab', amount))


def transfer_ba(amount):
    with lock_b:
        with lock_a:
            results.append(('ba', amount))
