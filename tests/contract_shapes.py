"""Structural view of a JSON schema, for comparing the schema an operation shows
the model with the grammar the provider enforces (ADR-0028 rule 1)."""
from __future__ import annotations

from typing import Any


def shape(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Every object in ``schema`` by path: its property names, required names
    and whether it is closed. Union branches at one path are merged; a nullable
    wrapper (``anyOf: [X, {"type": "null"}]``) counts as X; ``$ref`` is resolved."""
    defs = schema.get("$defs") or schema.get("definitions") or {}
    found: dict[str, dict[str, Any]] = {}

    def walk(node: Any, path: str, seen: frozenset[str]) -> None:
        if not isinstance(node, dict):
            return
        ref = node.get("$ref")
        if isinstance(ref, str):
            name = ref.rsplit("/", 1)[-1]
            if name in seen or name not in defs:
                return
            walk(defs[name], path, seen | {name})
            return
        for key in ("anyOf", "oneOf", "allOf"):
            for branch in node.get(key) or []:
                if isinstance(branch, dict) and branch.get("type") == "null":
                    continue
                walk(branch, path, seen)
        properties = node.get("properties")
        if isinstance(properties, dict) and properties:
            entry = found.setdefault(path, {"properties": set(), "required": set(), "closed": set()})
            entry["properties"] |= set(properties)
            entry["required"] |= set(node.get("required") or [])
            entry["closed"].add(node.get("additionalProperties") is False)
            for name, spec in properties.items():
                walk(spec, f"{path}.{name}", seen)
        items = node.get("items")
        if isinstance(items, dict):
            walk(items, f"{path}[]", seen)

    walk(schema, "$", frozenset())
    return found


def descriptions(schema: dict[str, Any]) -> dict[str, list[str]]:
    """Every ``description`` the schema shows, by path (same paths as ``shape``)."""
    defs = schema.get("$defs") or schema.get("definitions") or {}
    found: dict[str, set[str]] = {}

    def walk(node: Any, path: str, seen: frozenset[str]) -> None:
        if not isinstance(node, dict):
            return
        ref = node.get("$ref")
        if isinstance(ref, str):
            name = ref.rsplit("/", 1)[-1]
            if name not in seen and name in defs:
                walk(defs[name], path, seen | {name})
        if isinstance(node.get("description"), str):
            found.setdefault(path, set()).add(node["description"])
        for key in ("anyOf", "oneOf", "allOf"):
            for branch in node.get(key) or []:
                walk(branch, path, seen)
        properties = node.get("properties")
        if isinstance(properties, dict):
            for name, spec in properties.items():
                walk(spec, f"{path}.{name}", seen)
        if isinstance(node.get("items"), dict):
            walk(node["items"], f"{path}[]", seen)

    walk(schema, "$", frozenset())
    return {path: sorted(texts) for path, texts in sorted(found.items())}


def differences(shown: dict[str, Any], enforced: dict[str, Any]) -> list[str]:
    """Where the enforced grammar and the shown schema disagree, one line each."""
    a, b = shape(shown), shape(enforced)
    lines = []
    for path in sorted(set(a) | set(b)):
        if path not in a:
            lines.append(f"{path}: object enforced but not shown")
            continue
        if path not in b:
            lines.append(f"{path}: object shown but not enforced")
            continue
        for key in ("properties", "required", "closed"):
            if a[path][key] != b[path][key]:
                extra = b[path][key] - a[path][key]
                missing = a[path][key] - b[path][key]
                lines.append(f"{path} {key}: enforced adds {sorted(extra, key=str)}, drops {sorted(missing, key=str)}")
    return lines
