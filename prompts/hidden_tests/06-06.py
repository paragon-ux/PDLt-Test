"""Hidden tests for 06-06: tree serialization without recursion.

The output format is the original's: ``val(child,child,...)``, with "null" for
a missing node. A candidate is a one-argument function named like serialize,
names that say "iterative" (or similar) first. A deliverable may keep the
recursive original.

The candidate must:
- match the original's output on random trees;
- serialize a 100,000-deep chain (the prompt asks for depth 100,000+), with the
  interpreter's default recursion limit.

Trees are built from the deliverable's Node class when it has one.
"""
TEST_SECONDS = 60
_PREFER = ("iter", "fix", "stack", "safe", "new")


def CANDIDATES():
    found = [f for f in functions_named("serialize", params=1) if "serial" in f.__name__.lower()]
    return sorted(found, key=lambda f: (not any(w in f.__name__.lower() for w in _PREFER), f.__name__))


class _Node:
    def __init__(self, val, children=None):
        self.val = val
        self.children = children or []


def _node_class():
    cls = NS.get("Node")
    if isinstance(cls, type):
        try:
            probe = cls(1)
            if hasattr(probe, "children") and hasattr(probe, "val"):
                return cls
        except Exception:  # noqa: BLE001
            pass
    return _Node


def _make(val):
    node = _node_class()(val)
    if node.children is None:
        node.children = []
    return node


def _expected(node):
    if node is None:
        return "null"
    return f"{node.val}(" + ",".join(_expected(c) for c in node.children) + ")"


def test_small_trees_match_the_original_format(f):
    import random

    assert f(None) == "null"
    leaf = _make(7)
    assert f(leaf) == "7()"
    rng = random.Random(9)
    for _ in range(60):
        nodes = [_make(0)]
        for i in range(1, rng.randint(1, 30)):
            node = _make(i)
            rng.choice(nodes).children.append(node)
            nodes.append(node)
        assert f(nodes[0]) == _expected(nodes[0])


def test_deep_chain(f):
    import sys

    sys.setrecursionlimit(1000)
    depth = 100_000
    root = current = _make(1)
    for i in range(2, depth + 1):
        child = _make(i)
        current.children.append(child)
        current = child
    out = f(root)
    assert isinstance(out, str)
    assert out.startswith("1(2(3(") and out.endswith(f"{depth}()" + ")" * (depth - 1)), (out[:40], out[-40:])
    assert len(out) == sum(len(str(i)) + 2 for i in range(1, depth + 1))


TESTS = [test_small_trees_match_the_original_format, test_deep_chain]
