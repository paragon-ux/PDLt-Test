"""Hidden tests for 03-03: a fixed-block pool with a free list in its buffer.

From the prompt:
- N blocks of B bytes in one fixed buffer;
- allocate() -> int returns a free block's offset, or raises PoolExhausted;
- free(offset) returns the block;
- double frees are detected;
- the free list is embedded in the buffer.

The candidate is a class with allocate and free, built from N and B. These are
matched by parameter name (size words mean B; count words mean N), else taken
positionally as (N, B).

Offsets may be byte offsets (multiples of B) or block indices, as long as one
convention is used throughout. Exhaustion must raise an exception whose class is
named like PoolExhausted. A double free must raise. The pool must hold a byte
buffer of at least N*B bytes (bytearray, memoryview or array).
"""
TEST_SECONDS = 30
N, B = 8, 16


def CANDIDATES():
    return classes_with("allocate", "free")


def _make(C, n=N, b=B):
    import inspect

    try:
        params = [p for p in inspect.signature(C).parameters.values()
                  if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)]
    except (TypeError, ValueError):
        params = []
    kwargs = {}
    for p in params:
        name = p.name.lower()
        if "size" in name or name in ("b", "block_bytes", "bytes_per_block", "width"):
            kwargs[p.name] = b
        elif any(w in name for w in ("num", "count", "capacity", "total")) or name in ("n", "blocks", "nblocks"):
            kwargs[p.name] = n
    if len(kwargs) == 2:
        return C(**kwargs)
    return C(n, b)


def _offsets(pool, count):
    return [pool.allocate() for _ in range(count)]


def _convention(offsets, n=N, b=B):
    if set(offsets) == {i * b for i in range(n)}:
        return "bytes"
    if set(offsets) == set(range(n)):
        return "index"
    return None


def _is_exhausted(exc):
    names = [k.__name__.lower() for k in type(exc).__mro__]
    return any("exhaust" in name for name in names)


def test_allocates_every_block_then_exhausts(C):
    pool = _make(C)
    offsets = _offsets(pool, N)
    assert all(isinstance(o, int) and not isinstance(o, bool) for o in offsets), offsets
    assert len(set(offsets)) == N and _convention(offsets), f"offsets {sorted(offsets)}"
    try:
        extra = pool.allocate()
    except Exception as exc:  # noqa: BLE001 - the type is checked below
        assert _is_exhausted(exc), f"raised {type(exc).__name__}, not PoolExhausted"
    else:
        raise AssertionError(f"allocation N+1 returned {extra!r}")


def test_free_and_reallocate_cycles(C):
    import random

    pool = _make(C)
    offsets = _offsets(pool, N)
    convention = _convention(offsets)
    universe = set(offsets)
    held = set(offsets)
    rng = random.Random(11)
    for _ in range(3000):
        if held and (rng.random() < 0.5 or len(held) == N):
            o = rng.choice(sorted(held))
            pool.free(o)
            held.remove(o)
        elif len(held) < N:
            o = pool.allocate()
            assert o in universe and o not in held, (o, sorted(held))
            held.add(o)
    assert convention


def test_double_free_is_detected(C):
    pool = _make(C)
    a, b = pool.allocate(), pool.allocate()
    pool.free(a)
    try:
        pool.free(a)
    except Exception:  # noqa: BLE001 - any raised error is detection
        pass
    else:
        raise AssertionError("freeing the same block twice was accepted")
    # The pool is still consistent afterwards.
    pool.free(b)
    again = _offsets(pool, N)
    assert len(set(again)) == N


def test_holds_a_fixed_byte_buffer(C):
    import array

    pool = _make(C)
    sizes = []
    for value in vars(pool).values():
        if isinstance(value, (bytearray, memoryview)):
            sizes.append(value.nbytes if isinstance(value, memoryview) else len(value))
        elif isinstance(value, array.array):
            sizes.append(len(value) * value.itemsize)
    assert any(s >= N * B for s in sizes), f"no buffer of {N * B} bytes among {sizes}"


def test_other_sizes(C):
    for n, b in ((1, 8), (3, 32), (64, 8)):
        pool = _make(C, n, b)
        offsets = [pool.allocate() for _ in range(n)]
        assert _convention(offsets, n, b), (n, b, sorted(offsets))
        try:
            pool.allocate()
        except Exception as exc:  # noqa: BLE001
            assert _is_exhausted(exc)
        else:
            raise AssertionError(f"pool of {n} gave a block past its capacity")


TESTS = [test_allocates_every_block_then_exhausts, test_free_and_reallocate_cycles, test_double_free_is_detected,
         test_holds_a_fixed_byte_buffer, test_other_sizes]
