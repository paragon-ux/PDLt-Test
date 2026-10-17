"""Hidden tests for 06-03: the observer leak, fixed.

Candidates pair a batch function (named like process_batch, taking an emitter
and a batch) with an emitter class (one with an emit method). Names that say
"fixed" (or similar) come first, since a deliverable may keep the original too.

A candidate passes if, over 2,000 calls with one shared emitter:
- every call returns its own batch doubled, in order;
- the live instances of the deliverable's other classes (the processors) stay
  bounded;
- the emitter's own storage stays bounded (dead weak references kept forever
  are still a leak);
- the emitter still delivers to a subscriber that is alive.
"""
TEST_SECONDS = 40
_PREFER = ("fix", "correct", "safe", "weak", "new", "good")
_SUBSCRIBE = ("on", "subscribe", "add_listener", "add_observer", "register", "listen", "attach")


class _Pair:
    def __init__(self, batch_fn, emitter_cls):
        self.batch_fn, self.emitter_cls = batch_fn, emitter_cls
        self.__name__ = f"{batch_fn.__name__}/{emitter_cls.__name__}"


def CANDIDATES():
    batch_fns = [f for f in functions_named("process_batch", params=2) if "batch" in f.__name__.lower()]
    emitters = [c for c in classes_with("emit") if any(callable(getattr(c, s, None)) for s in _SUBSCRIBE)]
    pairs = [_Pair(f, c) for f in batch_fns for c in emitters]

    def rank(p):
        name = p.__name__.lower()
        return (not any(w in name for w in _PREFER), name)

    return sorted(pairs, key=rank)


def _live_instances(exclude):
    import gc

    gc.collect()
    return sum(1 for o in gc.get_objects()
               if type(o).__module__ == "deliverable" and isinstance(type(o), type) and type(o) is not exclude
               and not isinstance(o, type))


def _storage(obj):
    """Entries held in the emitter's attributes, one level into dict values."""
    total = 0
    for value in state_of(obj).values():
        try:
            items = list(value.values()) if hasattr(value, "values") and callable(value.values) else [value]
        except Exception:  # noqa: BLE001
            continue
        for item in items:
            try:
                total += len(item)
            except TypeError:
                total += 1
    return total


def _make_emitter(cls):
    return construct(cls)


def test_results_are_correct(p):
    emitter = _make_emitter(p.emitter_cls)
    for i in range(50):
        batch = list(range(i, i + 5))
        assert list(p.batch_fn(emitter, batch)) == [x * 2 for x in batch], i


def test_no_growth_over_many_calls(p):
    emitter = _make_emitter(p.emitter_cls)
    for _ in range(20):
        p.batch_fn(emitter, [1, 2, 3])
    base_objects, base_storage = _live_instances(p.emitter_cls), _storage(emitter)
    for i in range(2000):
        p.batch_fn(emitter, [i, i + 1])
    grown_objects = _live_instances(p.emitter_cls) - base_objects
    grown_storage = _storage(emitter) - base_storage
    assert grown_objects <= 5, f"{grown_objects} more live deliverable objects after 2,000 calls"
    assert grown_storage <= 5, f"emitter storage grew by {grown_storage} entries after 2,000 calls"


def test_live_subscriber_still_receives(p):
    emitter = _make_emitter(p.emitter_cls)
    seen = []

    class Sink:
        def handle(self, value):
            seen.append(value)

    sink = Sink()
    for name in _SUBSCRIBE:
        method = getattr(emitter, name, None)
        if callable(method):
            method("data", sink.handle)
            break
    p.batch_fn(emitter, [5])
    emitter.emit("data", 7)
    assert 7 in seen, f"a subscribed, live listener received {seen}"


TESTS = [test_results_are_correct, test_no_growth_over_many_calls, test_live_subscriber_still_receives]
