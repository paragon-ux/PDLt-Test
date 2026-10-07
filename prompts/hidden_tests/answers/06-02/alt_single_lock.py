# Correct with a different interface: one lock guards the shared state, so there
# is no second lock to order.
import threading

transfer_lock = threading.Lock()
ledger = []


def safe_transfer_ab(amount):
    with transfer_lock:
        ledger.append(('ab', amount))


def safe_transfer_ba(amount):
    with transfer_lock:
        ledger.append(('ba', amount))
