"""Hidden tests for 02-06: union-find with union-by-rank and save()/restore() rollback.

From the prompt:
- make_set(x), find(x) and union(x, y);
- save() captures the state; restore() reverts to the last saved state;
- nested save/restore sequences, so saved states nest like a stack.
"""
TEST_SECONDS = 15


def CANDIDATES():
    return classes_with("make_set", "find", "union", "save", "restore")


def _same(d, a, b):
    return d.find(a) == d.find(b)


def _sets(n, C):
    d = construct(C)
    for x in range(n):
        d.make_set(x)
    return d


def test_basic_connectivity(C):
    d = _sets(8, C)
    d.union(0, 1)
    d.union(2, 3)
    d.union(1, 3)
    assert _same(d, 0, 2) and _same(d, 1, 3)
    assert not _same(d, 0, 4) and not _same(d, 5, 6)


def test_restore_undoes_unions_since_save(C):
    d = _sets(6, C)
    d.union(0, 1)
    d.save()
    d.union(1, 2)
    d.union(3, 4)
    assert _same(d, 0, 2) and _same(d, 3, 4)
    d.restore()
    assert _same(d, 0, 1)
    assert not _same(d, 0, 2) and not _same(d, 3, 4)


def test_nested_save_restore(C):
    d = _sets(6, C)
    d.save()              # level 1: all separate
    d.union(0, 1)
    d.save()              # level 2: {0,1}
    d.union(2, 3)
    d.union(1, 2)
    assert _same(d, 0, 3)
    d.restore()           # back to {0,1}
    assert _same(d, 0, 1) and not _same(d, 0, 2) and not _same(d, 2, 3)
    d.union(4, 5)
    d.restore()           # back to all separate
    assert not _same(d, 0, 1) and not _same(d, 4, 5)


def test_many_unions_then_rollback(C):
    import random

    rng = random.Random(3)
    d = _sets(200, C)
    pairs = [(rng.randrange(200), rng.randrange(200)) for _ in range(150)]
    for a, b in pairs[:75]:
        d.union(a, b)
    before = [d.find(x) for x in range(200)]
    groups_before = {(x, y) for x in range(0, 200, 7) for y in range(0, 200, 11) if before[x] == before[y]}
    d.save()
    for a, b in pairs[75:]:
        d.union(a, b)
    d.restore()
    after = [d.find(x) for x in range(200)]
    groups_after = {(x, y) for x in range(0, 200, 7) for y in range(0, 200, 11) if after[x] == after[y]}
    assert groups_before == groups_after


TESTS = [test_basic_connectivity, test_restore_undoes_unions_since_save, test_nested_save_restore,
         test_many_unions_then_rollback]
