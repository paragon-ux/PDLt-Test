import threading

lock_a = threading.Lock()
lock_b = threading.Lock()
results = []


def transfer_ab(amount):
    with lock_a:
        with lock_b:
            results.append(('ab', amount))


def transfer_ba(amount):
    # Same global order as transfer_ab: lock_a, then lock_b.
    with lock_a:
        with lock_b:
            results.append(('ba', amount))
