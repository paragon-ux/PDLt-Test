"""One test per TARGET_ARCHITECTURE invariant, I-1 to I-12 (GOAL T1.4; plan 1.3, 1.5, 1.6).

Where today's code breaks an invariant that a later phase fixes, the case is listed in
``tests/architecture_exceptions.json`` with the phase and task that remove it. Each test
computes the cases that occur and requires them to equal the listed ones: a new violation
fails, and so does a fixed one that is still listed. I-12 keeps the list from growing.
An invariant whose mechanism a later phase builds is listed with a ``probe`` (the
function that phase adds); the test fails once the probe exists until its check is
written here and the exception removed.
"""
from __future__ import annotations

import ast
import hashlib
import importlib
import json
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import BaseModel, ConfigDict, Field
from pydantic_core import PydanticUndefined

from pdl_taskmaster.providers.fixtures import build_recorded_fixture_from_vendored
from pdl_taskmaster.providers.recorded import ReplayMissError
from pdl_taskmaster.runtime.context_compiler import ContextCompiler
from pdl_taskmaster.runtime.origins import Declared, Origin
from pdl_taskmaster.runtime.output_contracts import CONTRACT_KEY, contract
from pdl_taskmaster.runtime.result_ir import render_instructions
from pdl_taskmaster.runtime.session_engine import SessionEngine

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "pdl_taskmaster"
EXCEPTIONS = Path("tests") / "architecture_exceptions.json"
FIXTURE = ROOT / "tests" / "fixtures" / "recorded-cases.json"
CONTRACTS = (ROOT / "contracts", PACKAGE / "contracts")
SOLVER_OPERATIONS = ("EXECUTE", "EXECUTE_UNCONFIRMED")
# What a solver may see of model output: its own role's earlier attempts (section 4.7).
SOLVER_ROLE = frozenset({"EXECUTE", "EXECUTE_UNCONFIRMED", "EMIT_RESULT_IR"})
# The packages whose code makes host decisions (I-4 scan).
DECISION_PACKAGES = ("runtime", "verification", "controller", "host")


def _registry() -> dict:
    return json.loads((ROOT / EXCEPTIONS).read_text(encoding="utf-8"))


def _listed(invariant: str) -> dict[str, dict]:
    prefix = invariant + ":"
    return {e["id"][len(prefix):]: e for e in _registry()["exceptions"] if e["id"].startswith(prefix)}


def _contract(base: Path = ROOT / "contracts") -> dict:
    return json.loads((base / "EXECUTION_CONTRACT.json").read_text(encoding="utf-8"))


def _resolves(probe: str) -> bool:
    module, _, attribute = probe.partition(":")
    try:
        return hasattr(importlib.import_module(module), attribute)
    except ModuleNotFoundError:
        return False


def _awaiting(invariant: str, key: str, check: str) -> None:
    """An invariant whose mechanism a later phase builds: listed, with its probe absent."""
    entry = _listed(invariant).get(key)
    if entry is None:
        pytest.fail(f"{invariant} has neither an exception nor its check: write {check} in this test")
    assert not _resolves(entry["probe"]), (
        f"{entry['probe']} exists: write {check} in this test and remove {entry['id']} ({entry['task']})")


# I-1 ---------------------------------------------------------------------------------

class _VerifiedSys1:
    is_configured = True
    model = "invariants-sys1"

    def call(self, request):
        name = next(iter(request.questions))
        choice, other = ("APPLY_PROTOCOL", "BYPASS") if name == "route" else ("VERIFIED_EXECUTION", "STANDARD_EXECUTION")
        return {"answers": {name: {"choice": choice, "confidence": 0.97,
                                   "probabilities": {choice: 0.97, other: 0.03}}}}, 1.0


class _Captured(Exception):
    pass


_REPLIES = {
    "BOOTSTRAP_ANALYSIS": {"kind": "ANALYSIS", "task_summary": "Compute the stated value.", "approach_notes": "",
                           "risk_notes": "", "task_entities": []},
    "DRAFT_PROMPT": {"kind": "PROMPT", "prompt_body": "COMPUTE the stated value\nRETURN the value",
                     "approach_handoff": "NONE"},
    "DRAFT_PLAN": {"neutral_plan_body": "DERIVE the value\nEMIT the value"},
}


def _solver_requests() -> list:
    """The first solver request of each route, in a verified-execution session."""
    captured: list = []

    def model_call(request):
        if request.operation in SOLVER_OPERATIONS:
            captured.append(request)
            raise _Captured
        return json.dumps(_REPLIES[request.operation])

    sessions = (({}, ("$confirm-with-pseudocode Compute the sum of 3, 4 and 5.", "/confirm", "/confirm")),
                ({"no_review": True}, ("Compute the sum of 3, 4 and 5.",)))
    for options, turns in sessions:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            engine = SessionEngine(str(ROOT), model_call, available_execution_tools=None, workspace_root=tmp,
                                   sys1_client=_VerifiedSys1(), **options)
            try:
                for turn in turns:
                    engine.handle_user_message(turn)
            except _Captured:
                pass
    assert sorted(r.operation for r in captured) == sorted(SOLVER_OPERATIONS)
    return captured


def test_i1_every_value_has_exactly_one_declared_origin() -> None:
    for base in CONTRACTS:
        for name, spec in _contract(base)["operations"].items():
            symbols = set(spec["include"]) | set(spec.get("optional_include", []))
            assert symbols == set(spec.get("origins") or {}), (base, name)
            for text in spec["origins"].values():
                Declared.parse(text)
    # One origin per value: a symbol declared USER carries no host-rendered text.
    channel = render_instructions([], repo_root=ROOT, evidence_paths=["execution://body", "execution://witness"],
                                  requires_verified_execution=True)
    mixed = set()
    for request in _solver_requests():
        inputs = request.projection.document["operation_inputs"]
        for symbol, declared in request.manifest["symbol_origins"].items():
            if declared == Origin.USER.value and channel in str(inputs.get(symbol) or ""):
                mixed.add(symbol)
    assert mixed == set(_listed("I-1"))


# I-2 and I-3 -------------------------------------------------------------------------

def _solver_model_inputs(contract: dict) -> dict[str, set[str]]:
    """Solver inputs written by another operation's model: symbol -> solver operations."""
    found: dict[str, set[str]] = {}
    for operation in SOLVER_OPERATIONS:
        for symbol, text in contract["operations"][operation]["origins"].items():
            declared = Declared.parse(text)
            if declared.origin is Origin.MODEL and not set(declared.producers) <= SOLVER_ROLE:
                found.setdefault(symbol, set()).add(operation)
    return found


def test_i2_task_authority_comes_only_from_user_and_host_values() -> None:
    contract = _contract()
    # Mechanically through I-3: besides I-3's listed cases, every solver input is USER,
    # HOST or PUBLISHED, or the solver's own earlier output.
    assert set(_solver_model_inputs(contract)) <= set(_listed("I-3"))
    # Standards that still grant drafted artifacts authority are tracked by their exact text.
    applied = {r for operation in SOLVER_OPERATIONS for r in contract["operations"][operation]["requirements"]}
    registry = ContextCompiler(ROOT).registry
    for requirement_id, entry in _listed("I-2").items():
        assert requirement_id in applied, f"{requirement_id} no longer applies to a solver: remove its exception"
        text = registry.select([requirement_id])[0].text
        assert hashlib.sha256(text.encode("utf-8")).hexdigest() == entry["clause_sha256"], (
            f"{requirement_id} changed: if it no longer grants a drafted artifact authority, remove its exception")


def test_i3_no_solver_input_is_another_operations_model_text() -> None:
    for base in CONTRACTS:
        assert set(_solver_model_inputs(_contract(base))) == set(_listed("I-3")), base


def test_i3_a_new_model_symbol_in_a_solver_operation_is_caught() -> None:
    contract = _contract()
    contract["operations"]["EXECUTE"]["origins"]["NEW_DRAFT"] = "MODEL:DRAFT_PLAN"
    assert _solver_model_inputs(contract)["NEW_DRAFT"] == {"EXECUTE"}


# I-4 ---------------------------------------------------------------------------------

def _decision_text_sites(source: str, module: str) -> set[str]:
    """Top-level definitions (functions, methods, assignments) that use the ``re`` or
    ``regex`` module, or test a literal phrase with ``in``: ``<kind>:<module>:<name>``."""
    tree = ast.parse(source)
    aliases, functions = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            aliases |= {a.asname or a.name for a in node.names if a.name in ("re", "regex")}
        elif isinstance(node, ast.ImportFrom) and node.module in ("re", "regex"):
            functions |= {a.asname or a.name for a in node.names}

    def kinds(node: ast.AST) -> set[str]:
        found = set()
        for n in ast.walk(node):
            if (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id in aliases) or (
                    isinstance(n, ast.Name) and n.id in functions):
                found.add("regex")
            if (isinstance(n, ast.Compare) and any(isinstance(o, (ast.In, ast.NotIn)) for o in n.ops)
                    and isinstance(n.left, ast.Constant) and isinstance(n.left.value, str) and " " in n.left.value):
                found.add("phrase")
        return found

    sites = set()

    def visit(prefix: str, body: list) -> None:
        for top in body:
            if isinstance(top, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(top, ast.ClassDef):
                visit(prefix + top.name + ".", top.body)
                continue
            if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = top.name
            elif isinstance(top, (ast.Assign, ast.AnnAssign)):
                target = top.targets[0] if isinstance(top, ast.Assign) else top.target
                name = target.id if isinstance(target, ast.Name) else ast.unparse(target)
            else:
                name = type(top).__name__
            sites.update(f"{kind}:{module}:{prefix}{name}" for kind in kinds(top))

    visit("", tree.body)
    return sites


def test_i4_no_regex_or_phrase_test_on_a_decision_path() -> None:
    found = set()
    for package in DECISION_PACKAGES:
        for path in sorted((PACKAGE / package).rglob("*.py")):
            found |= _decision_text_sites(path.read_text(encoding="utf-8"), path.relative_to(PACKAGE).as_posix())
    host_formats = {e["id"][len("I-4:"):] for e in _registry()["not_decision_text"]}
    listed = set(_listed("I-4"))
    assert not listed & host_formats
    assert found - listed - host_formats == set(), "a regex or phrase test on a decision path (I-4)"
    assert (listed | host_formats) - found == set(), "listed I-4 sites that no longer occur: remove them"


def test_i4_the_scan_finds_regexes_and_phrase_tests() -> None:
    source = ("import re as rx\nfrom re import search\nP = rx.compile('a')\n"
              "class C:\n    def m(self, t):\n        return 'no such thing' in t\n"
              "def f(t):\n    return search('b', t)\n")
    assert _decision_text_sites(source, "m.py") == {"regex:m.py:P", "phrase:m.py:C.m", "regex:m.py:f"}


# I-5, I-6, I-7 -----------------------------------------------------------------------

def test_i5_every_risk_combination_has_exactly_one_disposition() -> None:
    _awaiting("I-5", "disposition", "the exhaustive table test over dispose()")


def test_i6_units_tile_each_message_and_quoted_spans_are_exact() -> None:
    _awaiting("I-6", "tiling", "the tiling and span-containment tests")


def test_i7_host_directed_and_payload_units_enter_no_projection() -> None:
    _awaiting("I-7", "exclusion", "the projection exclusion test")


# I-8 ---------------------------------------------------------------------------------

def _semantic_fields(models: dict[str, type]) -> tuple[set[str], set[str]]:
    """Fields marked ``contract(semantic=True)``, and those of them with a default other
    than absence (None)."""
    marked, defaulted = set(), set()
    for name, model in models.items():
        for field_name, field in model.model_fields.items():
            extra = field.json_schema_extra if isinstance(field.json_schema_extra, dict) else {}
            if not (extra.get(CONTRACT_KEY) or {}).get("semantic"):
                continue
            key = f"wire_payloads.{name}.{field_name}"
            marked.add(key)
            if field.default_factory is not None or field.default not in (PydanticUndefined, None):
                defaulted.add(key)
    return marked, defaulted


def _wire_models() -> dict[str, type]:
    import pdl_taskmaster.runtime.wire_payloads as wire

    return {name: obj for name, obj in vars(wire).items()
            if isinstance(obj, type) and issubclass(obj, BaseModel) and obj.__module__ == wire.__name__}


def test_i8_a_semantic_wire_field_has_no_default() -> None:
    marked, defaulted = _semantic_fields(_wire_models())
    assert {"wire_payloads.TaskEntity.polarity", "wire_payloads.TaskEntity.relation"} <= marked  # F6's fields
    assert defaulted == set(_listed("I-8"))


def test_i8_the_scan_finds_a_semantic_default() -> None:
    class Probe(BaseModel):
        model_config = ConfigDict(extra="forbid")
        stated: str = Field(default="known", json_schema_extra=contract(semantic=True))
        absent: str | None = Field(default=None, json_schema_extra=contract(semantic=True))
        plain: str = "free"

    assert _semantic_fields({"Probe": Probe}) == (
        {"wire_payloads.Probe.stated", "wire_payloads.Probe.absent"}, {"wire_payloads.Probe.stated"})


# I-9, I-10, I-11 ---------------------------------------------------------------------

def test_i9_runs_record_their_code_and_every_full_request(tmp_path: Path) -> None:
    import run_catalogue
    import test_reasoning_wire as wire

    provenance = run_catalogue.code_provenance(ROOT)
    assert len(provenance["commit"] or "") == 40 and provenance["dirty"] == bool(provenance["diff"].strip())
    wire._run_stub(tmp_path, {})
    attempts = [attempt for path in tmp_path.rglob("call-trace.jsonl")
                for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
                for attempt in json.loads(line)["attempts"]]
    assert attempts and all(a.get("request_file") and a.get("request_sha256") for a in attempts)


def test_i10_a_change_to_the_provider_request_alone_is_a_replay_miss() -> None:
    worker = build_recorded_fixture_from_vendored(ROOT, FIXTURE)
    entry = next(e for e in json.loads(FIXTURE.read_text(encoding="utf-8"))["entries"] if "provider_request" in e)
    request = SimpleNamespace(operation=entry["operation"], prompt=entry["prompt_text"])
    assert worker.call(request).text == entry["response"]
    real = worker.request_builder
    worker.request_builder = lambda r: {**real(r), "max_output_tokens": real(r)["max_output_tokens"] + 1}
    with pytest.raises(ReplayMissError):
        worker.call(request)


def test_i11_an_ungraded_outcome_is_never_a_pass() -> None:
    import graders
    import run_catalogue

    result = {"id": "08-01", "category": "logic_and_reasoning", "difficulty": "easy", "verdict": "CLOSED_SUCCESS",
              "expected_stage": "CLOSED_SUCCESS", "elapsed_seconds": 1.0,
              "ground_truth_grade": {"grade": graders.NA}, "regression_ref": None}
    assert run_catalogue.outcome_class(result) == "UNGRADED" and not run_catalogue.is_prompt_pass(result)
    _awaiting("I-11", "adversarial-outcomes", "the complied/contained/refused outcome test")


# I-12 --------------------------------------------------------------------------------

def _git(*args: str) -> str:
    try:
        done = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, encoding="utf-8")
    except FileNotFoundError:
        pytest.skip("git is not available")
    if done.returncode != 0:
        pytest.skip("not a git checkout")
    return done.stdout


def test_i12_the_exceptions_never_gain_an_entry() -> None:
    """Every committed version of the list holds every current entry: entries only leave."""
    current = _registry()
    for commit in _git("log", "--format=%H", "--", EXCEPTIONS.as_posix()).split():
        committed = json.loads(_git("show", f"{commit}:{EXCEPTIONS.as_posix()}"))
        for key in ("exceptions", "not_decision_text"):
            added = {e["id"] for e in current[key]} - {e["id"] for e in committed[key]}
            assert not added, f"{key} gained {sorted(added)} since {commit[:8]}: fix the code instead (I-12)"
        assert set(committed["landed_phases"]) <= set(current["landed_phases"]), commit[:8]


def test_i12_every_exception_names_a_phase_that_has_not_landed() -> None:
    registry = _registry()
    ids = [e["id"] for e in registry["exceptions"] + registry["not_decision_text"]]
    assert len(ids) == len(set(ids))
    landed = set(registry["landed_phases"])
    for entry in registry["exceptions"]:
        assert entry["phase"] in range(1, 7) and entry["phase"] not in landed, entry["id"]
        assert entry["task"] and entry["reason"], entry["id"]
    assert all(entry["reason"] for entry in registry["not_decision_text"])
