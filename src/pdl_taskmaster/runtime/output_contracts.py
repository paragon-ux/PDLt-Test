"""One output contract per operation (ADR-0028 rule 1, IMPL-0001).

The Pydantic payload model of each operation (wire_payloads.OPERATION_PAYLOAD_MODELS)
is the only definition of its output. Two views are generated from it:

- ``prompt_schema``: the ``output_schema`` the model reads in the projection;
- ``grammar_schema``: the decoding constraint sent to the provider, which is the
  prompt schema without its descriptions and the keywords decoding engines reject.

Both views apply the same structural form (``ContractForm``), so a key the provider
enforces is always a key the model was shown. The host validates every reply
against the Pydantic model whatever grammar was sent (ADR-0028 rule 5).

What the model is shown beyond Pydantic's structure is declared in the models with
``contract(...)`` (the ``x-contract`` key): descriptions, advisory keywords, and
required or closed overrides where the host is deliberately more lenient than the
contract. Pydantic's own titles, defaults and docstring descriptions are never shown.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CONTRACT_KEY = "x-contract"
UNION_WRAPPER = "outcome"

# Keywords a decoding engine does not take; the grammar view drops them (the prompt
# view keeps the advisory ones, e.g. minLength).
_GRAMMAR_DROPPED_KEYWORDS = ("description", "title", "default", "minLength", "maxLength", "minItems", "maxItems",
                             "uniqueItems", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
                             "pattern", "format", "multipleOf")
# Keywords the strict form drops (strict structured-output modes reject them).
_STRICT_DROPPED_KEYWORDS = ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "pattern", "format",
                            "default", "multipleOf")
_UNREPRESENTABLE = object()
_FREE_FORM_OBJECT: dict[str, Any] = {"type": "object", "additionalProperties": True}


def contract(**keywords: Any) -> dict[str, Any]:
    """``json_schema_extra`` for a model or field: what the contract shows beyond the
    Pydantic structure. Keys replace the generated ones at that node."""
    return {CONTRACT_KEY: keywords}


@dataclass(frozen=True)
class ContractForm:
    """How an operation's output is constrained for one call.

    grammar: ``schema`` (the JSON-schema grammar), ``json`` (JSON mode, no schema) or
    ``none``. strict_all_required: every property required, optional ones nullable
    (providers whose strict mode needs it). free_form_objects: whether open objects
    may be sent (providers that require closed objects drop them)."""

    grammar: str = "schema"
    strict_all_required: bool = False
    free_form_objects: bool = True


DEFAULT_FORM = ContractForm()


def contract_schema(operation: str) -> dict[str, Any] | None:
    """The operation's contract: its Pydantic model's schema with ``$ref`` inlined,
    discriminator tags required in every variant, objects closed unless declared
    open, and the ``x-contract`` annotations applied. None for an operation with no
    payload model."""
    from pydantic import TypeAdapter

    from pdl_taskmaster.runtime.wire_payloads import OPERATION_PAYLOAD_MODELS

    model = OPERATION_PAYLOAD_MODELS.get(operation)
    if model is None:
        return None
    raw = TypeAdapter(model).json_schema()
    return _normalize(raw, raw.get("$defs") or {})


def _normalize(node: Any, defs: dict[str, Any]) -> Any:
    if isinstance(node, list):
        return [_normalize(item, defs) for item in node]
    if not isinstance(node, dict):
        return node
    ref = node.get("$ref")
    if isinstance(ref, str) and ref.rsplit("/", 1)[-1] in defs:
        merged = {**defs[ref.rsplit("/", 1)[-1]], **{k: v for k, v in node.items() if k != "$ref"}}
        if CONTRACT_KEY in node and CONTRACT_KEY in defs[ref.rsplit("/", 1)[-1]]:
            # Field-level annotations refine the model's own.
            merged[CONTRACT_KEY] = {**defs[ref.rsplit("/", 1)[-1]][CONTRACT_KEY], **node[CONTRACT_KEY]}
        return _normalize(merged, defs)
    result: dict[str, Any] = {}
    for key, value in node.items():
        if key in ("$defs", "title", "description", "default", "discriminator", CONTRACT_KEY):
            continue
        if key == "properties" and isinstance(value, dict):
            # Property names are data: a field called "description" survives.
            result[key] = {name: _normalize(spec, defs) for name, spec in value.items()}
        else:
            result[key] = _normalize(value, defs)
    tag = (node.get("discriminator") or {}).get("propertyName")
    for branch in (result.get("oneOf") or result.get("anyOf") or []) if tag else []:
        if isinstance(branch, dict) and tag in (branch.get("properties") or {}):
            branch["required"] = list(dict.fromkeys([*(branch.get("required") or []), tag]))
    if isinstance(result.get("properties"), dict) and result["properties"]:
        result.setdefault("additionalProperties", False)
    result.update(node.get(CONTRACT_KEY) or {})
    return result


def prompt_schema(operation: str, form: ContractForm = DEFAULT_FORM) -> dict[str, Any] | None:
    """The output_schema the model reads, in the structural form of this call."""
    schema = contract_schema(operation)
    if schema is None or form.grammar != "schema":
        return schema
    schema = _wrap_top_level_union(schema)
    if form.strict_all_required:
        schema = _strict_schema(schema, free_form_objects=form.free_form_objects)
    return schema


def grammar_schema(operation: str, form: ContractForm = DEFAULT_FORM) -> dict[str, Any] | None:
    """The decoding constraint for this call: the prompt schema without what decoding
    engines reject. None unless the form sends a schema."""
    if form.grammar != "schema":
        return None
    schema = prompt_schema(operation, form)
    return None if schema is None else _grammar_view(schema)


def is_union_wrapped(schema: Any) -> bool:
    return isinstance(schema, dict) and list((schema.get("properties") or {})) == [UNION_WRAPPER]


def _grammar_view(node: Any) -> Any:
    if isinstance(node, list):
        return [_grammar_view(item) for item in node]
    if not isinstance(node, dict):
        return node
    result: dict[str, Any] = {}
    for key, value in node.items():
        if key in _GRAMMAR_DROPPED_KEYWORDS:
            continue
        if key == "properties" and isinstance(value, dict):
            result[key] = {name: _grammar_view(spec) for name, spec in value.items()}
        else:
            result[key] = _grammar_view(value)
    if "const" in result:
        result["enum"] = [result.pop("const")]
        result.setdefault("type", "string")
    if "oneOf" in result:
        result["anyOf"] = result.pop("oneOf")
    return result


def _wrap_top_level_union(schema: Any) -> Any:
    """Strict providers accept only one object at the top of a response schema
    (Groq: no anyOf/oneOf there; Cerebras: no discriminator anywhere), but accept a
    union nested inside one. A top-level union is therefore sent, and shown, as
    {"outcome": <the union>}, keeping every variant separate: merging them let a
    PROMPT reply see the blocked variant's blocking_basis, and the model filled it
    (probe 20261001-142720). The worker unwraps "outcome" before the host reads it."""
    if not isinstance(schema, dict):
        return schema
    variants = schema.get("anyOf") or schema.get("oneOf")
    if not isinstance(variants, list):
        return schema
    # The union's own annotations (its description) stay at the top.
    rest = {k: v for k, v in schema.items() if k not in ("anyOf", "oneOf", "type")}
    return {**rest, "type": "object", "properties": {UNION_WRAPPER: {"anyOf": variants}},
            "required": [UNION_WRAPPER], "additionalProperties": False}


def _strict_schema(node: Any, *, free_form_objects: bool = False) -> Any:
    """Strict structured-output form (Groq strict mode, Cerebras): every object with
    declared properties is closed and lists all its properties as required; an
    optional property becomes nullable instead. A free-form object is sent open when
    the providers accept one (free_form_objects); otherwise it cannot be expressed
    and is left out: an optional property or union branch holding one is dropped.
    The host validates the reply against the exact Pydantic model, where a null for
    a defaulted field means "not given" (wire_payloads.WireModel)."""
    result = _strictify(node, free_form_objects)
    return {"type": "object", "properties": {}, "required": [], "additionalProperties": False} \
        if result is _UNREPRESENTABLE else result


def _strictify(node: Any, free_form_objects: bool = False) -> Any:
    if not isinstance(node, dict):
        return node
    node = {k: v for k, v in node.items() if k not in _STRICT_DROPPED_KEYWORDS}
    for union_key in ("anyOf", "oneOf"):
        if union_key in node:
            branches = [b for b in (_strictify(b, free_form_objects) for b in node[union_key])
                        if b is not _UNREPRESENTABLE]
            if not branches:
                return _UNREPRESENTABLE
            rest = {k: v for k, v in node.items() if k != union_key}
            return {**rest, union_key: branches} if len(branches) > 1 else {**rest, **branches[0]}
    if node.get("type") == "array" and "items" in node:
        items = _strictify(node["items"], free_form_objects)
        return _UNREPRESENTABLE if items is _UNREPRESENTABLE else {**node, "items": items}
    if node.get("type") == "object" or "properties" in node:
        properties = node.get("properties")
        if not properties:
            return dict(_FREE_FORM_OBJECT) if free_form_objects else _UNREPRESENTABLE
        required = set(node.get("required") or [])
        strict_properties: dict[str, Any] = {}
        for name, spec in properties.items():
            converted = _strictify(spec, free_form_objects)
            if converted is _UNREPRESENTABLE:
                if name in required:
                    return _UNREPRESENTABLE
                continue
            if name not in required and not _is_nullable(converted):
                converted = {"anyOf": [converted, {"type": "null"}]}
            strict_properties[name] = converted
        return {**node, "type": "object", "properties": strict_properties,
                "required": list(strict_properties), "additionalProperties": False}
    return node


def _is_nullable(spec: Any) -> bool:
    if not isinstance(spec, dict):
        return False
    if spec.get("type") == "null" or (isinstance(spec.get("type"), list) and "null" in spec["type"]):
        return True
    return any(isinstance(b, dict) and b.get("type") == "null" for b in (spec.get("anyOf") or spec.get("oneOf") or []))
