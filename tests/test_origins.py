"""Every model-call input has a declared origin (TARGET_ARCHITECTURE I-1; GOAL T1.1)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from pdl_taskmaster.runtime.context_compiler import ContextCompiler
from pdl_taskmaster.runtime.origins import Declared, Origin, OriginMismatch, Sourced
from pdl_taskmaster.runtime.session_engine import SessionEngine

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "recorded-cases.json"
CONTRACT = ROOT / "contracts" / "EXECUTION_CONTRACT.json"


def test_every_symbol_of_every_operation_declares_its_origin() -> None:
    for base in (ROOT / "contracts", ROOT / "src" / "pdl_taskmaster" / "contracts"):
        operations = json.loads((base / "EXECUTION_CONTRACT.json").read_text(encoding="utf-8"))["operations"]
        for name, spec in operations.items():
            symbols = set(spec["include"]) | set(spec.get("optional_include", []))
            declared = spec.get("origins") or {}
            assert symbols == set(declared), (base, name, sorted(symbols ^ set(declared)))
            for text in declared.values():
                Declared.parse(text)  # well formed: an origin, and producers only for MODEL


def test_every_assembled_input_carries_an_origin_in_the_recorded_sessions() -> None:
    """Walks every operation the recorded cases reach and checks each assembled input."""
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    seen: list[str] = []
    for case, turns in fixture["case_turns"].items():
        recorded = [e for e in fixture["entries"] if e["source"].split(":")[0] == case]
        position = 0

        def model_call(request, _recorded=recorded):
            nonlocal position
            entry = _recorded[position]
            position += 1
            inputs = request.projection.document["operation_inputs"]
            origins = request.manifest["symbol_origins"]
            assert set(inputs) == set(origins), (request.operation, sorted(set(inputs) ^ set(origins)))
            seen.append(request.operation)
            return entry["response"]

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            engine = SessionEngine(str(ROOT), model_call, available_execution_tools=None, workspace_root=tmp,
                                   higher_priority_constraints="constraints")
            for turn in turns:
                engine.handle_user_message(turn)
    assert {"BOOTSTRAP_ANALYSIS", "DRAFT_PROMPT", "DRAFT_PLAN", "EXECUTE"} <= set(seen)


def _execute_values(prompt_body: str) -> dict:
    return {"CONFIRMED_PROMPT_BODY": prompt_body, "CONFIRMED_PLAN_BODY": "PLAN", "REQUIRED_TASK_INPUTS": None,
            "SUPPLIED_EXECUTION_INPUT_SOURCE": "request", "AVAILABLE_EXECUTION_TOOLS": []}


def test_a_sourced_value_must_match_its_slot() -> None:
    compiler = ContextCompiler(ROOT)
    drafted = Sourced("PROMPT", Origin.MODEL, "DRAFT_PROMPT")
    projection = compiler.compile("EXECUTE", _execute_values(drafted))
    assert projection.manifest["symbol_origins"]["CONFIRMED_PROMPT_BODY"] == "MODEL:DRAFT_PROMPT|REVISE_PROMPT"
    assert projection.document["operation_inputs"]["CONFIRMED_PROMPT_BODY"] == "PROMPT"  # same bytes
    with pytest.raises(OriginMismatch):
        compiler.compile("EXECUTE", _execute_values(Sourced("PROMPT", Origin.USER)))
    with pytest.raises(OriginMismatch):  # a model value from an operation the slot does not name
        compiler.compile("EXECUTE", _execute_values(Sourced("PROMPT", Origin.MODEL, "EXECUTE")))


def test_a_symbol_without_a_declared_origin_is_refused(monkeypatch) -> None:
    compiler = ContextCompiler(ROOT)
    del compiler.execution_contract["operations"]["EXECUTE"]["origins"]["CONFIRMED_PLAN_BODY"]
    with pytest.raises(ValueError, match="origin_undeclared:EXECUTE:CONFIRMED_PLAN_BODY"):
        compiler.compile("EXECUTE", _execute_values("PROMPT"))


def test_origin_declarations_parse_strictly() -> None:
    assert Declared.parse("MODEL:DRAFT_PLAN|REVISE_PLAN").producers == ("DRAFT_PLAN", "REVISE_PLAN")
    assert Declared.parse("USER").origin is Origin.USER
    for bad in ("MODEL", "USER:DRAFT_PROMPT", "AGENT"):
        with pytest.raises(ValueError):
            Declared.parse(bad)
    with pytest.raises(ValueError):
        Sourced("text", Origin.MODEL)  # a model value names its producer
