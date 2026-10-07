"""Hidden tests for 03-05: a single-producer single-consumer ring buffer.

From the prompt:
- fixed capacity N, a power of 2;
- push(item) and pop() use no locks;
- push returns False when full; pop returns None when empty.

The candidate is a class with push and pop, built with the capacity (matched by
parameter name, else positionally). Any push result other than False counts as
success. A full buffer may hold N items, or N - 1 for the one-empty-slot design.

Every item of a two-thread run must arrive in order, with no duplicates or
drops. No lock, condition, semaphore or queue.Queue may be among the instance's
attributes.

Not detectable here: publishing the new index before writing the slot. Under
the GIL that race almost never fires, so a black-box run can't catch it; it is
left to review.
"""
TEST_SECONDS = 60
CAPACITY = 64


def CANDIDATES():
    return classes_with("push", "pop")


def _make(C, capacity=CAPACITY):
    import inspect

    try:
        params = list(inspect.signature(C).parameters.values())
    except (TypeError, ValueError):
        params = []
    for p in params:
        if any(w in p.name.lower() for w in ("cap", "size", "n", "len")):
            return C(**{p.name: capacity})
    return C(capacity)


def test_empty_full_and_fifo(C):
    q = _make(C)
    assert q.pop() is None
    pushed = 0
    while q.push(pushed) is not False:
        pushed += 1
        assert pushed <= CAPACITY, "push never reports full"
    assert pushed in (CAPACITY, CAPACITY - 1), f"held {pushed} items with capacity {CAPACITY}"
    assert [q.pop() for _ in range(pushed)] == list(range(pushed))
    assert q.pop() is None


def test_wraparound_single_thread(C):
    q = _make(C, 8)
    expected, nxt = [], 0
    import random

    rng = random.Random(2)
    for _ in range(5000):
        if rng.random() < 0.5:
            if q.push(nxt) is not False:
                expected.append(nxt)
                nxt += 1
        else:
            got = q.pop()
            if expected:
                assert got == expected.pop(0), got
            else:
                assert got is None


def test_two_threads_in_order(C):
    import threading
    import time

    q = _make(C)
    total = 50_000
    received = []

    def produce():
        i = 0
        while i < total:
            if q.push(i) is not False:
                i += 1
            else:
                time.sleep(0)

    def consume():
        while len(received) < total:
            item = q.pop()
            if item is None:
                time.sleep(0)
            else:
                received.append(item)

    threads = [threading.Thread(target=produce, daemon=True), threading.Thread(target=consume, daemon=True)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(50)
    assert not any(t.is_alive() for t in threads), f"stalled after {len(received)} items"
    assert received == list(range(total)), "items lost, duplicated or out of order"


def test_no_locks(C):
    import queue
    import threading

    lock_types = (type(threading.Lock()), type(threading.RLock()), threading.Condition, threading.Semaphore,
                  threading.Event, queue.Queue)
    q = _make(C)
    found = [k for k, v in vars(q).items() if isinstance(v, lock_types)]
    assert not found, f"lock-like attributes: {found}"


TESTS = [test_empty_full_and_fifo, test_wraparound_single_thread, test_two_threads_in_order, test_no_locks]
