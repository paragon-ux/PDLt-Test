"""Values a program writes out instead of computing (L113).

A value is written out when the program contains a literal expression for it:
constants, signed numbers, list, tuple and dict displays of them, f-strings whose
parts are all written out, and names bound exactly once to such an expression,
followed through any number of names. A value the program derives (a call, a loop,
a comprehension, arithmetic, a container it mutates) is not written out, even when
every operand is a literal of the program: a program that selects its answer from
input data it contains computes that answer.

Structure only (ADR-0018): the syntax tree is read, nothing is matched by pattern.
"""

from __future__ import annotations

import ast
from typing import Any

# Method calls that change the container they are called on.
_MUTATORS = frozenset({
    "append", "extend", "insert", "update", "add", "setdefault", "pop", "popitem", "remove", "discard",
    "clear", "sort", "reverse",
})
_CONVERSIONS = {-1: None, 115: str, 114: repr, 97: ascii}
_NOT_WRITTEN = object()


def _root_name(node: ast.expr) -> str | None:
    while isinstance(node, (ast.Subscript, ast.Attribute)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _bindings(tree: ast.AST) -> dict[str, list[ast.expr | None]]:
    """Every binding of every name, anywhere in the program; None is a binding to a
    value that is not an expression of the program (a parameter, a loop target, an
    import, a mutation of the container the name holds)."""
    bindings: dict[str, list[ast.expr | None]] = {}

    def bind(target: ast.AST, value: ast.expr | None) -> None:
        if isinstance(target, ast.Name):
            bindings.setdefault(target.id, []).append(value)
        elif isinstance(target, (ast.Tuple, ast.List)):
            paired = (isinstance(value, (ast.Tuple, ast.List)) and len(value.elts) == len(target.elts)
                      and not any(isinstance(e, ast.Starred) for e in (*target.elts, *value.elts)))
            for index, element in enumerate(target.elts):
                bind(element, value.elts[index] if paired else None)
        elif isinstance(target, ast.Starred):
            bind(target.value, None)
        elif isinstance(target, (ast.Subscript, ast.Attribute)):
            name = _root_name(target)
            if name is not None:
                bindings.setdefault(name, []).append(None)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                bind(target, node.value)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            bind(node.target, node.value)
        elif isinstance(node, (ast.AugAssign, ast.For, ast.AsyncFor, ast.comprehension, ast.NamedExpr)):
            bind(node.target, None)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars is not None:
                    bind(item.optional_vars, None)
        elif isinstance(node, ast.Delete):
            for target in node.targets:
                bind(target, None)
        elif isinstance(node, ast.arguments):
            for arg in (*node.posonlyargs, *node.args, *node.kwonlyargs, node.vararg, node.kwarg):
                if arg is not None:
                    bindings.setdefault(arg.arg, []).append(None)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bindings.setdefault(node.name, []).append(None)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bindings.setdefault((alias.asname or alias.name).split(".")[0], []).append(None)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            for name in node.names:
                bindings.setdefault(name, []).append(None)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bindings.setdefault(node.name, []).append(None)
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
            bindings.setdefault(node.name, []).append(None)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            bindings.setdefault(node.rest, []).append(None)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in _MUTATORS:
            name = _root_name(node.func.value)
            if name is not None:
                bindings.setdefault(name, []).append(None)
    return bindings


class _Folder:
    def __init__(self, tree: ast.AST) -> None:
        self.bindings = _bindings(tree)
        self.memo: dict[int, Any] = {}
        self.open: set[str] = set()  # names being followed: a cycle is not written out

    def fold(self, node: ast.AST | None) -> Any:
        if node is None:
            return _NOT_WRITTEN
        key = id(node)
        if key not in self.memo:
            self.memo[key] = self._fold(node)
        return self.memo[key]

    def _fold(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value if isinstance(node.value, (str, int, float, bool, type(None))) else _NOT_WRITTEN
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value = self.fold(node.operand)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return _NOT_WRITTEN
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, (ast.List, ast.Tuple)):
            items = [_NOT_WRITTEN if isinstance(e, ast.Starred) else self.fold(e) for e in node.elts]
            if any(item is _NOT_WRITTEN for item in items):
                return _NOT_WRITTEN
            return items if isinstance(node, ast.List) else tuple(items)
        if isinstance(node, ast.Dict):
            folded: dict[Any, Any] = {}
            for key_node, value_node in zip(node.keys, node.values):
                key, value = self.fold(key_node), self.fold(value_node)  # ``**spread`` has no key node
                if key is _NOT_WRITTEN or value is _NOT_WRITTEN:
                    return _NOT_WRITTEN
                try:
                    folded[key] = value
                except TypeError:
                    return _NOT_WRITTEN
            return folded
        if isinstance(node, ast.JoinedStr):
            parts = []
            for part in node.values:
                if isinstance(part, ast.FormattedValue):
                    value = self.fold(part.value)
                    spec = "" if part.format_spec is None else self.fold(part.format_spec)
                    convert = _CONVERSIONS.get(part.conversion)
                    if value is _NOT_WRITTEN or spec is _NOT_WRITTEN:
                        return _NOT_WRITTEN
                    try:
                        parts.append(format(convert(value) if convert else value, spec))
                    except (TypeError, ValueError):
                        return _NOT_WRITTEN
                else:
                    value = self.fold(part)
                    if not isinstance(value, str):
                        return _NOT_WRITTEN
                    parts.append(value)
            return "".join(parts)
        if isinstance(node, ast.Name) and node.id not in self.open:
            bound = self.bindings.get(node.id, [])
            if len(bound) != 1:
                return _NOT_WRITTEN
            self.open.add(node.id)
            try:
                return self._fold(bound[0]) if bound[0] is not None else _NOT_WRITTEN
            finally:
                self.open.discard(node.id)
        return _NOT_WRITTEN


def written_out_values(source: str) -> list[Any]:
    """The value of every expression the program writes out, in syntax-tree order.
    A program that does not parse writes out nothing the host can read."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, MemoryError, RecursionError):
        return []
    folder = _Folder(tree)
    values = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Constant, ast.UnaryOp, ast.List, ast.Tuple, ast.Dict, ast.JoinedStr, ast.Name)):
            try:
                value = folder.fold(node)
            except RecursionError:
                continue
            if value is not _NOT_WRITTEN:
                values.append(value)
    return values
