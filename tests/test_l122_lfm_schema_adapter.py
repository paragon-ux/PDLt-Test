"""L122: the LFM schema adapter (the user, 2026-10-15). Liquid rejects schemas nested more than 10 levels; for
``liquid/lfm`` only, nullable scalars are sent as type lists. The canonical schema and every other model's request
are unchanged, and the adapted schema accepts and rejects exactly the same instances. Offline; no model call."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator

from pdl_taskmaster.providers import model_adapters, model_capabilities
from pdl_taskmaster.providers.api_worker import ApiWorker
from pdl_taskmaster.runtime.output_contracts import EXECUTION_BRIEF_MODE, RESULT_IR_MODE, ContractForm, grammar_schema

ROOT = Path(__file__).resolve().parents[1]
LFM = "liquid/lfm-2.5-2.6b:free"
SCHEMAS = {
    "EXECUTE_UNCONFIRMED": grammar_schema("EXECUTE_UNCONFIRMED", ContractForm(grammar="schema"),
                                          frozenset({RESULT_IR_MODE})),
    "EXECUTE": grammar_schema("EXECUTE", ContractForm(grammar="schema"),
                              frozenset({RESULT_IR_MODE, EXECUTION_BRIEF_MODE})),
}
PROBES = [None, "x", 7, 1.5, True, [], {}]


def _depth(node) -> int:
    if not isinstance(node, dict):
        return 0
    children = list((node.get("properties") or {}).values())
    children += [node["items"]] if isinstance(node.get("items"), dict) else []
    children += node.get("anyOf") or []
    return 1 + max((_depth(c) for c in children), default=0)


def _paths_rewritten(original, adapted, path=()):
    """Paths whose node the adapter rewrote (an anyOf that became a type list)."""
    if isinstance(original, dict) and isinstance(adapted, dict):
        if "anyOf" in original and "anyOf" not in adapted:
            yield path
            return
        for key in original:
            if key in adapted:
                yield from _paths_rewritten(original[key], adapted[key], path + (key,))
    elif isinstance(original, list) and isinstance(adapted, list):
        for index, (a, b) in enumerate(zip(original, adapted)):
            yield from _paths_rewritten(a, b, path + (index,))


def _instances(schema):
    """A valid instance for the base choice of every union, then one per alternative branch of each union."""
    unions = []

    def gen(node, choice, trail=()):
        if "anyOf" in node:
            unions.append(trail) if trail not in unions else None
            return gen(node["anyOf"][choice.get(trail, 0)], choice, trail + ("anyOf",))
        types = node.get("type")
        kind = next((t for t in types if t != "null"), "null") if isinstance(types, list) else types
        if "enum" in node:
            return node["enum"][0]
        if kind == "object" or "properties" in node:
            return {name: gen(spec, choice, trail + (name,)) for name, spec in (node.get("properties") or {}).items()}
        if kind == "array":
            return [gen(node["items"], choice, trail + ("[]",))] if isinstance(node.get("items"), dict) else []
        return {"string": "x", "integer": 1, "number": 1.5, "boolean": True, "null": None}[kind]

    base = gen(schema, {})
    found = [base]
    for trail in list(unions):
        node = schema
        for step in trail:
            node = node["anyOf"][0] if step == "anyOf" else node["items"] if step == "[]" else node["properties"][step]
        for branch in range(1, len(node["anyOf"])):
            found.append(gen(schema, {trail: branch}))
    return found


def _set(instance, schema_path, value):
    """Set the instance location that a rewritten schema path describes, where the instance has it."""
    target = instance
    keys = [k for k in schema_path if k not in ("properties",)]
    for key in keys[:-1]:
        if key == "items":
            if not isinstance(target, list) or not target:
                return False
            target = target[0]
        elif isinstance(key, int) or key == "anyOf":
            continue
        else:
            if not isinstance(target, dict) or key not in target:
                return False
            target = target[key]
    if isinstance(target, dict) and keys[-1] in target:
        target[keys[-1]] = value
        return True
    return False


@pytest.mark.parametrize("operation", sorted(SCHEMAS))
def test_the_adapted_schema_accepts_and_rejects_the_same_instances(operation):
    original = SCHEMAS[operation]
    adapted = model_adapters.flatten_nullable_scalars(copy.deepcopy(original))
    rewritten = list(_paths_rewritten(original, adapted))
    assert rewritten, "nothing to flatten"
    before, after = Draft202012Validator(original), Draft202012Validator(adapted)
    checked = 0
    for instance in _instances(original):
        assert before.is_valid(instance), json.dumps(instance)[:300]
        assert after.is_valid(instance)
        for path in rewritten:
            for probe in PROBES:
                mutated = copy.deepcopy(instance)
                if _set(mutated, path, probe):
                    assert before.is_valid(mutated) == after.is_valid(mutated), (path, probe)
                    checked += 1
    assert checked > 50
    # Each rewritten node on its own, against every probe value.
    for path in rewritten:
        node_a, node_b = original, adapted
        for key in path:
            node_a, node_b = node_a[key], node_b[key]
        for probe in PROBES:
            assert Draft202012Validator(node_a).is_valid(probe) == Draft202012Validator(node_b).is_valid(probe)


def test_only_simple_scalar_unions_are_flattened():
    complex_union = {"anyOf": [{"type": "object", "properties": {"a": {"type": "string"}}}, {"type": "null"}]}
    enum_union = {"anyOf": [{"type": "string", "enum": ["a"]}, {"type": "null"}]}
    triple = {"anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "null"}]}
    for node in (complex_union, enum_union, triple):
        assert model_adapters.flatten_nullable_scalars(node) == node
    assert model_adapters.flatten_nullable_scalars({"anyOf": [{"type": "null"}, {"type": "integer"}]}) == {
        "type": ["integer", "null"]}


def test_the_depth_falls_and_only_lfm_is_adapted(monkeypatch):
    original = SCHEMAS["EXECUTE_UNCONFIRMED"]
    assert _depth(model_adapters.flatten_nullable_scalars(original)) < _depth(original)
    entries = {m: {"id": m, "supported_parameters": ["structured_outputs", "response_format"]}
               for m in (LFM, "dots-studio/dots-3-note-preview:free")}
    monkeypatch.setattr(model_capabilities, "model_list", lambda base_url, timeout: entries)
    request = SimpleNamespace(operation="EXECUTE_UNCONFIRMED", prompt="TASK")
    sent = {m: ApiWorker(model=m, repo_root=ROOT).build_request_body(request)[0]["text"]["format"]["schema"]
            for m in entries}
    canonical = grammar_schema("EXECUTE_UNCONFIRMED", ContractForm(grammar="schema"))  # a bare request: no modes
    assert sent["dots-studio/dots-3-note-preview:free"] == canonical  # unchanged
    assert sent[LFM] == model_adapters.flatten_nullable_scalars(canonical) != canonical
