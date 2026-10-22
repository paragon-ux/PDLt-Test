"""L147: the unconfirmed route's working notes state how the task is read and the method, not the result (UNC-03).
System 1 decides whether an attempt's notes are pre-conclusive; the decision is recorded on every attempt, and a test
run (``--stop-on-preconclusive-notes``, set by the catalogue runner) stops fail-closed at the first pre-conclusive
one. A general protocol rule: no prompt, category or benchmark logic. Offline; the worker and System 1 are scripted."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import run_catalogue
from pdl_taskmaster.controller.mechanical_controller import Stage
from pdl_taskmaster.host import repl
from pdl_taskmaster.providers.api_worker import ApiWorker
from pdl_taskmaster.providers.sys1.recipes.working_notes import CHECK, WorkingNotesRecipe
from pdl_taskmaster.runtime.run_settings import RunSettings
from pdl_taskmaster.runtime.session_engine import SessionEngine

ROOT = Path(__file__).resolve().parents[1]
REQUEST = "Two numbers x and y satisfy x + y = 10 and x - y = 2. Find x and explain why."
BODY = "x = 6, because adding the equations gives 2x = 12."


def _answer(choice: str, confidence: float) -> dict:
    other = "false" if choice == "true" else "true"
    return {"choice": choice, "confidence": confidence,
            "probabilities": {choice: confidence, other: round(1 - confidence, 4)}}


class Sys1:
    """Routes every request into the protocol; answers the working-notes question as scripted."""

    is_configured = True
    model = "fake-sys1"

    def __init__(self, notes: str | None = "true", confidence: float = 0.97, fail: bool = False):
        self.notes, self.confidence, self.fail = notes, confidence, fail
        self.notes_requests: list = []

    def call(self, request):
        name = next(iter(request.questions))
        if name == CHECK:
            self.notes_requests.append(request)
            if self.fail:
                raise RuntimeError("System 1 unavailable")
            return {"answers": {name: _answer(self.notes, self.confidence)}}, 1.0
        choice = "APPLY_PROTOCOL" if name == "route" else "STANDARD_EXECUTION"
        other = "BYPASS" if name == "route" else "VERIFIED_EXECUTION"
        return {"answers": {name: {"choice": choice, "confidence": 0.97,
                                   "probabilities": {choice: 0.97, other: 0.03}}}}, 1.0


def _model(calls: list):
    def model_call(req):
        calls.append(req.operation)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({"kind": "ANALYSIS", "task_summary": "Find x from the two equations.",
                               "approach_notes": "", "risk_notes": "", "task_entities": []})
        if req.operation == "EXECUTE_UNCONFIRMED":
            return json.dumps({"kind": "RESULT", "interpretation": "DETERMINE x from the two given equations",
                               "approach": "ADD the equations; SOLVE for x", "body": BODY})
        raise AssertionError(f"unexpected operation: {req.operation}")
    return model_call


def _run(tmp_path: Path, sys1: Sys1, *, stop: bool):
    calls: list = []
    engine = SessionEngine(ROOT, _model(calls), workspace_root=tmp_path, sys1_client=sys1, no_review=True)
    engine.stop_on_preconclusive_notes = stop
    response = engine.handle_user_message(REQUEST)
    events = [json.loads(line) for f in sorted(tmp_path.rglob("events.jsonl"))
              for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]
    outputs = sorted(tmp_path.rglob("stages/50_execution/output/current.json"))
    published = json.loads(outputs[-1].read_text(encoding="utf-8")) if outputs else {}
    deliverable = (outputs[-1].parent / "current.md").read_text(encoding="utf-8") if outputs else ""
    return engine, response, calls, events, published, deliverable


def _decisions(events: list) -> list:
    return [e["payload"] for e in events if e.get("kind") == "WORKING_NOTES_CONCLUSION"]


# The decision (System 1, ADR-0012 gating).

def test_the_question_carries_the_request_and_both_notes_and_nothing_else():
    request = WorkingNotesRecipe().build_request(
        {"source_request": "R", "interpretation": "I", "approach": "A", "other": "x"})
    assert request.state == {"source_request": "R", "interpretation": "I", "approach": "A"}
    assert list(request.questions) == [CHECK]
    assert list(request.questions[CHECK].choices) == ["true", "false"]


@pytest.mark.parametrize("choice,confidence,verdict,gated", [
    ("false", 0.95, "PRE_CONCLUSIVE", True),
    ("true", 0.95, "NEUTRAL", True),
    ("false", 0.60, "UNCERTAIN", False),
])
def test_a_confident_false_is_pre_conclusive_and_a_weak_answer_is_uncertain(choice, confidence, verdict, gated):
    result = WorkingNotesRecipe().parse_response({"answers": {CHECK: _answer(choice, confidence)}})
    assert (result.verdict, result.passed_gating) == (verdict, gated)


def test_a_missing_answer_is_uncertain():
    assert WorkingNotesRecipe().parse_response({"answers": {}}).verdict == "UNCERTAIN"


# The engine: recorded on every attempt; a test run stops at a pre-conclusive one.

def test_a_test_run_stops_fail_closed_at_pre_conclusive_notes(tmp_path: Path):
    sys1 = Sys1(notes="false")
    engine, response, calls, events, published, deliverable = _run(tmp_path, sys1, stop=True)
    assert calls == ["BOOTSTRAP_ANALYSIS", "EXECUTE_UNCONFIRMED"]  # no repair, no further call
    assert engine.controller.state.stage == Stage.CLOSED_CANCELLED
    assert engine.workspace.read_turn_status("turn_001")["status"] == "CLOSED_CANCELLED"
    assert response.closed and BODY not in response.text
    assert published["kind"] == "NOTES_PRECONCLUSIVE" and published["withheld_body"] == BODY
    assert published["decision"]["verdict"] == "PRE_CONCLUSIVE"
    assert BODY not in deliverable  # what a grader reads carries no deliverable
    assert [d["verdict"] for d in _decisions(events)] == ["PRE_CONCLUSIVE"]
    assert sys1.notes_requests[0].state["source_request"].strip() == REQUEST
    assert not any(e.get("kind") == "VERIFICATION_PASSED" for e in events)


def test_outside_a_test_run_the_decision_is_recorded_and_the_run_continues(tmp_path: Path):
    engine, response, calls, events, published, _ = _run(tmp_path, Sys1(notes="false"), stop=False)
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS
    assert BODY in response.text and published["kind"] == "RESULT"
    assert [d["verdict"] for d in _decisions(events)] == ["PRE_CONCLUSIVE"]


@pytest.mark.parametrize("sys1,fallback", [
    (Sys1(notes="true"), None),
    (Sys1(notes="false", confidence=0.6), "below_floor"),
    (Sys1(fail=True), "sys1_error:RuntimeError"),
])
def test_neutral_uncertain_or_unavailable_never_stops_a_test_run(tmp_path: Path, sys1: Sys1, fallback):
    engine, response, _, events, published, _ = _run(tmp_path, sys1, stop=True)
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS
    assert published["kind"] == "RESULT" and BODY in response.text
    assert [d["fallback"] for d in _decisions(events)] == [fallback]


# The rule reaches the model, and the setting reaches the engine from the CLI and the catalogue runner.

def test_the_execute_unconfirmed_guidance_states_the_rule():
    body = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT).build_request_body(
        SimpleNamespace(operation="EXECUTE_UNCONFIRMED", prompt="Analyse this task."))[0]
    assert "not the result" in body["instructions"] and "(UNC-03)" in body["instructions"]


def test_the_standard_states_the_rule():
    for root in (ROOT / "contracts", ROOT / "src" / "pdl_taskmaster" / "contracts"):
        text = (root / "standards" / "UNCONFIRMED_STANDARD.md").read_text(encoding="utf-8")
        unc03 = next(line for line in text.splitlines() if line.startswith("**UNC-03"))
        assert "do not state or assume the result" in unc03


def test_the_setting_is_validated_and_applied():
    with pytest.raises(ValueError):
        RunSettings(stop_on_preconclusive_notes="yes")
    engine = SimpleNamespace()
    RunSettings(stop_on_preconclusive_notes=True).apply(engine)
    assert engine.stop_on_preconclusive_notes is True
    assert RunSettings().stop_on_preconclusive_notes is False


def test_the_catalogue_runner_sets_it_on_the_unconfirmed_route_only(tmp_path: Path):
    def cmd(**settings):
        return run_catalogue.build_harness_command(tmp_path / "p.txt", "s", tmp_path / "t.txt", tmp_path / "d", "m",
                                                   "low", run_settings=settings)
    on = cmd(route="unconfirmed", stop_on_preconclusive_notes=True)
    assert repl._build_parser().parse_args(on[3:]).stop_on_preconclusive_notes is True
    assert "--stop-on-preconclusive-notes" not in cmd(route="unconfirmed", stop_on_preconclusive_notes=False)
    assert "--stop-on-preconclusive-notes" not in cmd(route="confirmed", stop_on_preconclusive_notes=True)
    assert repl._build_parser().parse_args([]).stop_on_preconclusive_notes is False


# A pre-conclusive stop halts the whole run: the catalogue runner and the study driver (the user, 2026-10-22: the
# failure is systemic, 'independent of arm').

def _result(prompt_id: str, halt: bool) -> dict:
    return {"id": prompt_id, "category": "logic_and_reasoning", "file": f"{prompt_id}.txt", "difficulty": "easy",
            "expected_routing": "PROTOCOL", "expected_stage": "CLOSED_SUCCESS", "ground_truth_status": "verified",
            "verdict": "CLOSED_CANCELLED" if halt else "CLOSED_SUCCESS", "exit_code": 1 if halt else 0,
            "timed_out": False, "elapsed_seconds": 1.0, "harness_peak_memory_mb": None, "start_time": "t",
            "session_id": "s", "transcript_file": f"results/{prompt_id}/transcript.txt", "ground_truth_check": None,
            "ground_truth_grade": {"grade": "FAIL" if halt else "PASS", "reason": "r"},
            "notes_preconclusive": halt, "pdl_rules_stressed": [], "tags": [], "regression_ref": None,
            "tester_note": None}


def test_the_catalogue_run_halts_entirely_at_the_first_pre_conclusive_stop(monkeypatch, tmp_path: Path):
    started = []

    def run_single_prompt(entry, *args, **kwargs):
        started.append(entry["id"])
        return _result(entry["id"], halt=True)

    monkeypatch.setattr(run_catalogue, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(run_catalogue, "code_provenance", lambda root=None: {
        "commit": "c", "dirty": False, "diff": "", "diff_sha256": None, "untracked": []})
    monkeypatch.setattr(run_catalogue, "run_single_prompt", run_single_prompt)
    monkeypatch.setattr("sys.argv", ["run_catalogue.py", "--prompt-id", "16-06,16-01", "--route", "unconfirmed"])
    with pytest.raises(SystemExit) as stopped:
        run_catalogue.main()
    assert stopped.value.code == run_catalogue.NOTES_HALT_EXIT
    assert len(started) == 1  # the second prompt never started
    (run_dir,) = (tmp_path / "runs").iterdir()
    meta = json.loads((run_dir / "RUN_META.json").read_text(encoding="utf-8"))
    assert meta["halted"]["after"] == 1 and meta["halted"]["of"] == 2
    assert meta["rules"]["stop_on_preconclusive_notes"] is True
    assert (run_dir / "HALTED.md").is_file()


def test_the_study_halts_entirely_and_refuses_to_resume(monkeypatch, tmp_path: Path):
    from experiments import matched_study
    from test_l145_study_tools import _config, _scripted_run

    config = _config(tmp_path)
    calls = _scripted_run(monkeypatch, config, {})
    scripted = matched_study.run_unit

    def run_unit(config, block, arm, attempt, logs):
        return {**scripted(config, block, arm, attempt, logs), "notes_halt": len(calls) == 2}

    monkeypatch.setattr(matched_study, "run_unit", run_unit)
    assert matched_study.cmd_run(config, type("A", (), {"max_blocks": None})()) == matched_study.NOTES_HALT_EXIT
    assert len(calls) == 2  # nothing after the halting unit
    assert matched_study.halt_path(config).is_file()
    monkeypatch.undo()
    assert any("halted" in problem for problem in matched_study.preflight(config, check_key=False))
