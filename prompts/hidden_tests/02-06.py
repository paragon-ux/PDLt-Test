"""Hidden tests for 02-06: a persistent red-black tree with path copying.

The prompt names three functions:
- insert(tree, key) -> new_tree;
- lookup(tree, key) -> bool;
- to_sorted_list(tree) -> list.

Two shapes are accepted:
- **module functions** over an empty tree (None, or the deliverable's own empty
  value or class);
- **an immutable tree class** whose methods take the key and return new trees.

Balance is checked by behaviour, not by inspecting nodes: 2,000 ascending
inserts must neither exhaust recursion nor take quadratic time.
"""
TEST_SECONDS = 30


class _Functions:
    __name__ = "module functions"

    def __init__(self, insert, lookup, to_list, empty):
        self.insert, self.lookup, self.to_list, self.empty = insert, lookup, to_list, empty


class _Methods:
    def __init__(self, cls):
        self.__name__ = cls.__name__
        self.empty = construct(cls)

    def insert(self, tree, key):
        return tree.insert(key)

    def lookup(self, tree, key):
        return tree.lookup(key)

    def to_list(self, tree):
        return tree.to_sorted_list()


def _empties():
    yield None
    for name in ("EMPTY", "Empty", "EMPTY_TREE", "NIL", "LEAF", "empty", "empty_tree"):
        value = NS.get(name)
        if value is not None:
            yield value() if callable(value) and not isinstance(value, type) else value


def CANDIDATES():
    insert, lookup, to_list = NS.get("insert"), NS.get("lookup"), NS.get("to_sorted_list")
    found = []
    if callable(insert) and callable(lookup) and callable(to_list):
        for empty in _empties():
            try:
                tree = insert(empty, 1)
                if lookup(tree, 1) and list(to_list(tree)) == [1]:
                    found.append(_Functions(insert, lookup, to_list, empty))
                    break
            except Exception:  # noqa: BLE001 - this empty value does not fit
                continue
    for cls in classes_with("insert", "lookup", "to_sorted_list"):
        try:
            found.append(_Methods(cls))
        except Exception:  # noqa: BLE001
            continue
    return found


def _build(api, keys):
    tree = api.empty
    for k in keys:
        tree = api.insert(tree, k)
    return tree


def test_membership_and_order(api):
    import random

    keys = list(range(0, 400, 3))
    random.Random(2).shuffle(keys)
    tree = _build(api, keys)
    assert list(api.to_list(tree)) == sorted(keys)
    assert all(api.lookup(tree, k) for k in keys)
    assert not any(api.lookup(tree, k) for k in (1, 2, 400, -3))


def test_persistence(api):
    t1 = _build(api, [10, 5, 15, 3, 7])
    snapshot = list(api.to_list(t1))
    t2 = api.insert(t1, 8)
    t3 = api.insert(t2, 1)
    assert list(api.to_list(t1)) == snapshot and not api.lookup(t1, 8)
    assert api.lookup(t2, 8) and not api.lookup(t2, 1)
    assert list(api.to_list(t3)) == [1, 3, 5, 7, 8, 10, 15]


def test_ascending_inserts_stay_balanced(api):
    tree = _build(api, range(2000))
    assert list(api.to_list(tree))[:5] == [0, 1, 2, 3, 4]
    assert api.lookup(tree, 1999) and api.lookup(tree, 0)


TESTS = [test_membership_and_order, test_persistence, test_ascending_inserts_stay_balanced]
