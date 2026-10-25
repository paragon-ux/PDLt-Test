"""L148: the A/B flag ``--withhold-execution-context`` keeps EXECUTE's instructions out of the earlier stages, and the
unconfirmed notes' scope reaches the model through the guidance and UNC-03. The System 1 stage-scope lint (L147,
L148) is removed (the user, 2026-10-22: System 1 is not reliable enough for this decision); no stage-scope question
reaches System 1 and nothing halts a run. Offline; the worker and System 1 are scripted."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import run_catalogue
from pdl_taskmaster.host import repl
from pdl_taskmaster.providers.api_worker import ApiWorker
from pdl_taskmaster.runtime.run_settings import RunSettings
from pdl_taskmaster.runtime.session_engine import SessionEngine

ROOT = Path(__file__).resolve().parents[1]
REQUEST = "Two numbers x and y satisfy x + y = 10 and x - y = 2. Find x and explain why."
BODY = "x = 6, because adding the equations gives 2x = 12."
PROMPT = "DETERMINE x from the two given equations"
PLAN = "ADD the two equations\nSOLVE the sum for x"


class Sys1:
    """Routes every request into the protocol; records every question it is asked."""

    is_configured = True
    model = "fake-sys1"

    def __init__(self):
        self.questions: list[str] = []

    def call(self, request):
        self.questions += list(request.questions)
        name = next(iter(request.questions))
        choice = "APPLY_PROTOCOL" if name == "route" else "STANDARD_EXECUTION"
        other = "BYPASS" if name == "route" else "VERIFIED_EXECUTION"
        return {"answers": {name: {"choice": choice, "confidence": 0.97,
                                   "probabilities": {choice: 0.97, other: 0.03}}}}, 1.0


def _model(calls: list, requests: list | None = None):
    def model_call(req):
        calls.append(req.operation)
        if requests is not None:
            requests.append(req)
        if req.operation == "INTERPRET_ACTIVATION":
            return json.dumps({"route": "APPLY_PROTOCOL", "response": None})
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({"kind": "ANALYSIS", "task_summary": "Find x from the two equations.",
                               "approach_notes": "", "risk_notes": "", "task_entities": []})
        if req.operation == "EXECUTE_UNCONFIRMED":
            return json.dumps({"kind": "RESULT", "interpretation": "DETERMINE x from the two given equations",
                               "approach": "ADD the equations; SOLVE for x", "body": BODY})
        if req.operation == "DRAFT_PROMPT":
            return json.dumps({"kind": "PROMPT", "prompt_body": PROMPT, "approach_handoff": "NONE"})
        if req.operation == "DRAFT_PLAN":
            return json.dumps({"neutral_plan_body": PLAN})
        raise AssertionError(f"unexpected operation: {req.operation}")
    return model_call


def _engine(tmp_path: Path, sys1: Sys1, *, no_review: bool = True, withhold: bool = False,
            requests: list | None = None):
    calls: list = []
    engine = SessionEngine(ROOT, _model(calls, requests), workspace_root=tmp_path, sys1_client=sys1,
                           no_review=no_review)
    engine.withhold_execution_context = withhold
    return engine, calls


def _events(tmp_path: Path) -> list:
    return [json.loads(line) for f in sorted(tmp_path.rglob("events.jsonl"))
            for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.mark.parametrize("no_review", [True, False])
def test_no_stage_scope_judgement_reaches_system_1(tmp_path: Path, no_review: bool):
    sys1 = Sys1()
    engine, calls = _engine(tmp_path, sys1, no_review=no_review)
    engine.handle_user_message(REQUEST)
    if not no_review:
        engine.handle_user_message("/confirm")
    assert not any(q.endswith("_scope") or "_entity_" in q for q in sys1.questions)
    assert not any(e.get("kind") in ("STAGE_SCOPE", "STAGE_CONCLUSIVE") for e in _events(tmp_path))
    assert ("EXECUTE_UNCONFIRMED" if no_review else "DRAFT_PLAN") in calls
    assert not hasattr(engine, "stop_on_conclusive")


def test_withholding_keeps_execution_context_out_of_the_earlier_stages_only(tmp_path: Path):
    def prompts(withhold: bool, root: Path) -> dict:
        requests: list = []
        engine, _ = _engine(root, Sys1(), no_review=False, withhold=withhold, requests=requests)
        engine.handle_user_message(REQUEST)
        engine.handle_user_message("/confirm")
        return {r.operation: r.prompt for r in requests}

    plain, withheld = prompts(False, tmp_path / "plain"), prompts(True, tmp_path / "withheld")
    assert "AVAILABLE_EXECUTION_TOOLS" in plain["BOOTSTRAP_ANALYSIS"]
    assert "AVAILABLE_EXECUTION_TOOLS" not in withheld["BOOTSTRAP_ANALYSIS"]
    assert '"EXEC-01"' in plain["DRAFT_PLAN"] and '"EXEC-01"' not in withheld["DRAFT_PLAN"]
    assert plain["DRAFT_PROMPT"] == withheld["DRAFT_PROMPT"]  # it received no execution content to withhold


def test_withholding_leaves_execute_unchanged(tmp_path: Path):
    def execute_prompt(withhold: bool, root: Path) -> str:
        requests: list = []
        engine, _ = _engine(root, Sys1(), withhold=withhold, requests=requests)
        engine.handle_user_message(REQUEST)
        return next(r.prompt for r in requests if r.operation == "EXECUTE_UNCONFIRMED")

    assert execute_prompt(False, tmp_path / "a") == execute_prompt(True, tmp_path / "b")


# The rule reaches the model; the settings reach the engine from the CLI and the catalogue runner.

def test_the_execute_unconfirmed_guidance_states_each_note_s_scope():
    body = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT).build_request_body(
        SimpleNamespace(operation="EXECUTE_UNCONFIRMED", prompt="Analyse this task."))[0]
    assert "not a method or the result" in body["instructions"] and "(UNC-03)" in body["instructions"]


def test_the_standard_states_each_note_s_scope():
    for root in (ROOT / "contracts", ROOT / "src" / "pdl_taskmaster" / "contracts"):
        text = (root / "standards" / "UNCONFIRMED_STANDARD.md").read_text(encoding="utf-8")
        unc03 = next(line for line in text.splitlines() if line.startswith("**UNC-03"))
        assert "without a method or the result" in unc03 and "without the result" in unc03


def test_the_setting_is_validated_and_applied():
    with pytest.raises(ValueError):
        RunSettings(withhold_execution_context=1)
    engine = SimpleNamespace()
    RunSettings(withhold_execution_context=True).apply(engine)
    assert engine.withhold_execution_context is True
    assert RunSettings().withhold_execution_context is False
    assert "stop_on_conclusive" not in RunSettings.__dataclass_fields__


def test_the_catalogue_runner_passes_the_flag_on_every_protocol_route(tmp_path: Path):
    def cmd(**settings):
        return run_catalogue.build_harness_command(tmp_path / "p.txt", "s", tmp_path / "t.txt", tmp_path / "d", "m",
                                                   "low", run_settings=settings)
    for route in ("unconfirmed", "confirmed"):
        parsed = repl._build_parser().parse_args(cmd(route=route, withhold_execution_context=True)[3:])
        assert parsed.withhold_execution_context is True
    assert "--withhold-execution-context" not in cmd(route="control", withhold_execution_context=True)
    assert repl._build_parser().parse_args([]).withhold_execution_context is False
    with pytest.raises(SystemExit):
        repl._build_parser().parse_args(["--stop-on-conclusive"])
