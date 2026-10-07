"""Hidden tests for 06-02: the corrected two-lock transfer program.

Candidates are pairs of the deliverable's transfer functions, one for each
direction (names containing "transfer" and "ab" / "ba"). Names that say "fixed"
(or similar) come first, since a deliverable may keep the original too.

**The deadlock interleaving, forced.** Every lock object the deliverable keeps at
module level is swapped for a wrapper that, on a thread's first acquisition, waits
briefly at a two-party barrier. One thread then runs the a-to-b transfer and one
the b-to-a transfer:
- the original code reliably deadlocks: each holds its first lock and waits for
  the other's;
- any correct fix finishes:
  - consistent ordering: the second thread blocks before the barrier, which
    times out;
  - a single lock: same;
  - timed acquisition with back-off: the waiter gives up and retries.

In both runs, a module-level ``results`` list, if the functions keep one, must
gain one entry per call: giving up on a busy lock and dropping the transfer
avoids the hang but is not a fix.

**A plain stress run** of 200 threads must also finish.
"""
TEST_SECONDS = 20
_PREFER = ("fix", "correct", "safe", "order", "new", "good")


class _Pair:
    def __init__(self, ab, ba):
        self.ab, self.ba = ab, ba
        self.__name__ = f"{ab.__name__}/{ba.__name__}"


def CANDIDATES():
    funcs = [f for f in functions_named(params=1) if "transfer" in f.__name__.lower()]
    funcs += [f for f in functions_named("transfer_ab", "transfer_ba") if f not in funcs]
    ab = [f for f in funcs if "ab" in f.__name__.lower().replace("transfer", "")]
    ba = [f for f in funcs if "ba" in f.__name__.lower().replace("transfer", "")]
    pairs = [_Pair(x, y) for x in ab for y in ba]

    def rank(p):
        name = p.__name__.lower()
        return (not any(w in name for w in _PREFER), name)

    return sorted(pairs, key=rank)


def _lock_types():
    import threading

    return (type(threading.Lock()), type(threading.RLock()))


class _Gate:
    """Wraps a lock: a thread's first acquisition of any wrapped lock meets a barrier."""

    def __init__(self, inner, barrier, local):
        self._inner, self._barrier, self._local = inner, barrier, local

    def acquire(self, blocking=True, timeout=-1):
        got = self._inner.acquire(blocking, timeout)
        if got and not getattr(self._local, "met", False):
            self._local.met = True
            try:
                self._barrier.wait(timeout=0.5)
            except Exception:  # noqa: BLE001 - a broken or timed-out barrier just lets it continue
                pass
        return got

    def release(self):
        self._inner.release()

    def locked(self):
        return self._inner.locked()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *exc):
        self.release()
        return False


def _gated():
    import threading

    barrier, local = threading.Barrier(2), threading.local()
    names = [k for k, v in NS.items() if isinstance(v, _lock_types())]
    for k in names:
        NS[k] = _Gate(NS[k], barrier, local)
    return names


def _restore(names):
    for k in names:
        if isinstance(NS[k], _Gate):
            NS[k] = NS[k]._inner


def test_forced_interleaving_finishes(p):
    import threading

    names = _gated()
    results = NS.get("results")
    before = len(results) if isinstance(results, list) else None
    try:
        assert names, "no module-level lock to exercise"
        threads = [threading.Thread(target=p.ab, args=(1,), daemon=True),
                   threading.Thread(target=p.ba, args=(2,), daemon=True)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(8)
        assert not any(t.is_alive() for t in threads), "deadlocked under the a-then-b / b-then-a interleaving"
        if before is not None and NS.get("results") is results:
            assert len(results) - before == 2, f"{len(results) - before} of 2 transfers recorded"
    finally:
        _restore(names)


def test_stress_finishes_and_records(p):
    import threading

    results = NS.get("results")
    before = len(results) if isinstance(results, list) else None
    threads = []
    for i in range(100):
        threads.append(threading.Thread(target=p.ab, args=(i,), daemon=True))
        threads.append(threading.Thread(target=p.ba, args=(i,), daemon=True))
    for t in threads:
        t.start()
    for t in threads:
        t.join(10)
    assert not any(t.is_alive() for t in threads), "threads still running after the stress run"
    if before is not None and NS.get("results") is results:
        assert len(results) - before == 200, (before, len(results))


TESTS = [test_forced_interleaving_finishes, test_stress_finishes_and_records]
