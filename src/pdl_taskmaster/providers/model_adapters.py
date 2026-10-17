"""Per-model adaptations of the decoding schema a request sends (L122). The canonical contract and the schema the
model is shown are unchanged; an adapter rewrites only the constraint sent to a provider whose schema support needs
it, into a form that accepts exactly the same instances.

Registered:
- ``liquid/lfm`` (Liquid's endpoint): "JSON Schema nesting cannot exceed 10 levels" (HTTP 400, 2026-10-15).
  A nullable scalar written as ``anyOf [{type: T}, {type: null}]`` costs a level; ``{type: [T, "null"]}`` accepts the
  same values. Only that simple form is rewritten; every other union stays an ``anyOf`` (the user, 2026-10-15).
"""
from __future__ import annotations

from typing import Any, Callable

SCALAR_TYPES = frozenset({"string", "number", "integer", "boolean"})


def flatten_nullable_scalars(node: Any) -> Any:
    """``anyOf [{type: T}, {type: null}]`` (either order, T a scalar type, nothing else in either branch) becomes
    ``{type: [T, "null"]}``, keeping the node's other keywords. Applied throughout; nothing else changes."""
    if isinstance(node, list):
        return [flatten_nullable_scalars(item) for item in node]
    if not isinstance(node, dict):
        return node
    result = {key: flatten_nullable_scalars(value) for key, value in node.items()}
    branches = result.get("anyOf")
    if isinstance(branches, list) and len(branches) == 2 and "type" not in result:
        null = [b for b in branches if b == {"type": "null"}]
        scalar = [b for b in branches if isinstance(b, dict) and set(b) == {"type"} and b["type"] in SCALAR_TYPES]
        if len(null) == 1 and len(scalar) == 1:
            rest = {key: value for key, value in result.items() if key != "anyOf"}
            return {**rest, "type": [scalar[0]["type"], "null"]}
    return result


SCHEMA_ADAPTERS: dict[str, Callable[[Any], Any]] = {"liquid/lfm": flatten_nullable_scalars}


def adapt_sent_schema(model: str, schema: Any) -> Any:
    """The decoding schema for ``model``: adapted when the model has a registered adapter, otherwise as given."""
    for prefix, adapter in SCHEMA_ADAPTERS.items():
        if model.lower().startswith(prefix):
            return adapter(schema)
    return schema
