"""Hidden tests for 05-07: Kahn's topological sort, reporting an actual cycle.

The input is an adjacency list over nodes 0..7: a dict {node: [successors]},
or a list of lists when the candidate only accepts that (decided on the DAG
case and then used for every case).
- **A DAG:** some node sequence in the result must be an ordering that
  respects every edge (a bare list, or one inside a returned tuple or dict).
- **A cyclic graph:** the report must contain an actual cycle, a node sequence
  whose consecutive edges, closing edge included, all exist.
  - It is accepted from an exception (its ``cycle``/``nodes``/``path``
    attribute, args or message) or from the return value.
  - A structured sequence must be exactly the cycle (a repeated closing node is
    allowed).
  - A message may carry other numbers, so any run of its integers that forms a
    cycle counts.
  - A bare "cycle exists" fails.

The cyclic graphs put each cycle out of sorted order and give it downstream
nodes, so listing the nodes left with in-degree > 0 does not happen to be a
cycle.
"""
TEST_SECONDS = 20


def CANDIDATES():
    return functions_named("topological_sort", "kahn", "kahns_algorithm", "topo_sort", "kahn_topological_sort",
                           "kahn_sort", "topological_order", "kahn_toposort", "kahn_topo_sort", params=1)


DAG = {0: [1, 2], 1: [3], 2: [3, 4], 3: [5], 4: [5, 6], 5: [7], 6: [7], 7: []}
CYCLIC = {0: [1], 1: [4], 2: [1, 3], 3: [5], 4: [2], 5: [6], 6: [7], 7: []}
MORE_CYCLIC = [
    {0: [0], 1: []},
    {0: [1], 1: [0], 2: [0]},
    {0: [1], 1: [2], 2: [4], 3: [5], 4: [3], 5: [2], 6: [], 7: [0]},
]


def _as_list(graph):
    return [list(graph[n]) for n in range(len(graph))]


def _caller(f):
    """Call with a dict, unless only the list form gives a valid DAG ordering."""
    try:
        if any(_valid_order(seq, DAG) for seq in _sequences(f({k: list(v) for k, v in DAG.items()}))):
            return lambda g: f({k: list(v) for k, v in g.items()})
    except Exception:  # noqa: BLE001 - try the list form
        pass
    return lambda g: f(_as_list(g))


def _call(f, graph):
    try:
        return _caller(f)(graph)
    except Exception as exc:  # noqa: BLE001 - raising is an accepted report
        return exc


def _node(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value)
    return None


def _valid_order(order, graph):
    pos = {n: i for i, n in enumerate(order)}
    return len(pos) == len(order) == len(graph) and set(order) == set(graph) and \
        all(pos[u] < pos[v] for u, vs in graph.items() for v in vs)


def _is_cycle(seq, graph):
    seq = list(seq)
    if len(seq) >= 2 and seq[0] == seq[-1]:
        seq = seq[:-1]
    if not seq or len(set(seq)) != len(seq):
        return False
    return all(b in graph.get(a, ()) for a, b in zip(seq, seq[1:] + seq[:1]))


def _sequences(value, depth=0):
    """Every structured node sequence inside a returned value or a raised exception."""
    if depth > 4:
        return
    if isinstance(value, BaseException):
        for attr in ("cycle", "nodes", "path"):
            if hasattr(value, attr):
                yield from _sequences(getattr(value, attr), depth + 1)
        for arg in value.args:
            yield from _sequences(arg, depth + 1)
    elif isinstance(value, dict):
        for v in value.values():
            yield from _sequences(v, depth + 1)
    elif isinstance(value, (list, tuple)):
        nodes = [_node(v) for v in value]
        if nodes and None not in nodes:
            yield nodes
        for v in value:
            if isinstance(v, (list, tuple, dict)):
                yield from _sequences(v, depth + 1)


def _messages(value):
    if isinstance(value, BaseException):
        yield str(value)
        for arg in value.args:
            if isinstance(arg, str):
                yield arg
    elif isinstance(value, str):
        yield value
    elif isinstance(value, (list, tuple)):
        for v in value:
            if isinstance(v, str):
                yield v
    elif isinstance(value, dict):
        for v in value.values():
            if isinstance(v, str):
                yield v


def _reports_cycle(result, graph):
    import re

    if any(_is_cycle(seq, graph) for seq in _sequences(result)):
        return True
    for message in _messages(result):
        tokens = [int(t) for t in re.findall(r"(?<![\w.])\d+(?![\w.])", message)]
        for i in range(len(tokens)):
            for j in range(i + 1, len(tokens) + 1):
                if _is_cycle(tokens[i:j], graph):
                    return True
    return False


def test_dag_ordering(f):
    result = _caller(f)(DAG)
    assert any(_valid_order(seq, DAG) for seq in _sequences(result)), repr(result)[:200]


def test_reports_an_actual_cycle(f):
    result = _call(f, CYCLIC)
    assert _reports_cycle(result, CYCLIC), f"no valid cycle in {result!r}"[:300]


def test_more_cycles(f):
    for graph in MORE_CYCLIC:
        result = _call(f, graph)
        assert _reports_cycle(result, graph), (graph, repr(result)[:200])


TESTS = [test_dag_ordering, test_reports_an_actual_cycle, test_more_cycles]
