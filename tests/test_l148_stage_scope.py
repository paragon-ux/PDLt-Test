"""L147, L148: every artifact is judged against the scope of the stage that produced it. A bootstrap analysis does
nothing but extract the request faithfully; a prompt (and the unconfirmed interpretation) names neither a method nor
the result; a plan (and the unconfirmed approach) names the method, not the result. System 1 answers with a category;
the host sums its probability over the out-of-scope categories (the user's mapping, fixed before calibration). The
decision is recorded on every stage; a test run (``--stop-on-conclusive``, set by the catalogue runner) stops
fail-closed at the first conclusive artifact, and the catalogue run or study halts entirely. The A/B flag
``--withhold-execution-context`` keeps EXECUTE's instructions out of the earlier stages. General protocol rules: no
prompt, category or benchmark logic. Offline; the worker and System 1 are scripted."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import run_catalogue
from pdl_taskmaster.controller.mechanical_controller import Stage
from pdl_taskmaster.host import repl
from pdl_taskmaster.providers.api_worker import ApiWorker
from pdl_taskmaster.providers.sys1.recipes import stage_scope
from pdl_taskmaster.providers.sys1.recipes.stage_scope import (
    CONCLUSIVE, IN_SCOPE, NONE, SCOPES, UNCERTAIN, Item, StageScopeRecipe, verdict_from,
)
from pdl_taskmaster.runtime.run_settings import RunSettings
from pdl_taskmaster.runtime.session_engine import STAGE_CONCLUSIVE_KIND, SessionEngine

ROOT = Path(__file__).resolve().parents[1]
REQUEST = "Two numbers x and y satisfy x + y = 10 and x - y = 2. Find x and explain why."
BODY = "x = 6, because adding the equations gives 2x = 12."
PROMPT = "DETERMINE x from the two given equations"
PLAN = "ADD the two equations\nSOLVE the sum for x"
SCOPE_OF = {"analysis": "bootstrap", "prompt": "prompt", "plan": "plan", "interpretation": "prompt",
            "approach": "plan"}


def _probabilities(scope: str, category: str, p: float = 0.97) -> dict:
    choices = SCOPES[scope].choices
    rest = (1 - p) / (len(choices) - 1)
    return {c: (p if c == category else rest) for c in choices}


class Sys1:
    """Routes every request into the protocol; answers each stage-scope question as scripted (by artifact key: a
    category, or a probabilities dict), in scope otherwise."""

    is_configured = True
    model = "fake-sys1"

    def __init__(self, scripted: dict | None = None, fail: bool = False):
        self.scripted, self.fail = scripted or {}, fail
        self.scope_requests: list = []

    def call(self, request):
        name = next(iter(request.questions))
        if name.endswith("_scope"):
            self.scope_requests.append(request)
            if self.fail:
                raise RuntimeError("System 1 unavailable")
            answers = {}
            for question in request.questions:
                key = question[: -len("_scope")]
                scope = SCOPE_OF[key]
                wanted = self.scripted.get(key, NONE)
                probabilities = wanted if isinstance(wanted, dict) else _probabilities(scope, wanted)
                choice = max(probabilities, key=probabilities.get)
                answers[question] = {"choice": choice, "confidence": probabilities[choice],
                                     "probabilities": probabilities}
            return {"answers": answers}, 1.0
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


def _engine(tmp_path: Path, sys1: Sys1, *, stop: bool, no_review: bool = True, withhold: bool = False,
            requests: list | None = None):
    calls: list = []
    engine = SessionEngine(ROOT, _model(calls, requests), workspace_root=tmp_path, sys1_client=sys1,
                           no_review=no_review)
    engine.stop_on_conclusive = stop
    engine.withhold_execution_context = withhold
    return engine, calls


def _record(tmp_path: Path):
    events = [json.loads(line) for f in sorted(tmp_path.rglob("events.jsonl"))
              for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]
    outputs = sorted(tmp_path.rglob("stages/50_execution/output/current.json"))
    published = json.loads(outputs[-1].read_text(encoding="utf-8")) if outputs else {}
    deliverable = (outputs[-1].parent / "current.md").read_text(encoding="utf-8") if outputs else ""
    return events, published, deliverable


def _scopes(events: list) -> list:
    return [(e["payload"]["operation"], e["payload"]["verdict"]) for e in events if e.get("kind") == "STAGE_SCOPE"]


# The decision: categories, and the host's sum over the out-of-scope set (the user's gate).

def test_each_artifact_gets_one_question_with_its_scope_categories():
    request = StageScopeRecipe([Item("interpretation", "prompt", "I"), Item("approach", "plan", "A")]).build_request(
        {"source_request": "R", "other": "x"})
    assert request.state == {"source_request": "R", "interpretation": "I", "approach": "A"}
    assert list(request.questions) == ["interpretation_scope", "approach_scope"]
    assert list(request.questions["interpretation_scope"].choices) == [*SCOPES["prompt"].out_of_scope, NONE]
    assert "NAMES_METHOD" in SCOPES["prompt"].out_of_scope and "NAMES_METHOD" not in SCOPES["plan"].out_of_scope
    assert "Any amount counts" in request.questions["approach_scope"].instructions  # what is present, not dominant
    with pytest.raises(ValueError):
        StageScopeRecipe([Item("x", "execute", "")])


@pytest.mark.parametrize("probabilities,verdict", [
    ({"STATES_RESULT": 0.9, "NAMES_METHOD": 0.1}, CONCLUSIVE),
    ({"STATES_RESULT": 0.45, "ASSUMES_RESULT": 0.4, "NAMES_METHOD": 0.15}, CONCLUSIVE),  # a split between two outs
    ({"NONE": 0.9, "STATES_RESULT": 0.1}, IN_SCOPE),
    ({"NONE": 0.5, "STATES_RESULT": 0.5}, UNCERTAIN),  # a real split between none and out of scope
])
def test_the_gate_sums_the_out_of_scope_set(probabilities, verdict):
    choice = max(probabilities, key=probabilities.get)
    answer = {"choice": choice, "probabilities": probabilities}
    assert verdict_from(answer, SCOPES["plan"], stage_filter=1.01)["verdict"] == verdict  # the gate alone


def test_the_stage_filter_marks_another_stage_s_content_above_its_threshold():
    """The user's deterministic filter: any other stage's mass at the calibrated threshold is conclusive, below the
    0.80 gate too; the bootstrap's own-stage category (a misread) counts only toward the gate."""
    mixed = {"choice": "NONE", "probabilities": {"NONE": 0.7, "STATES_RESULT": 0.2, "ASSUMES_RESULT": 0.1}}
    assert verdict_from(mixed, SCOPES["plan"], stage_filter=0.25)["verdict"] == CONCLUSIVE  # EXECUTE mass 0.3
    assert verdict_from(mixed, SCOPES["plan"], stage_filter=0.35)["verdict"] == UNCERTAIN
    split = {"choice": "NONE", "probabilities": {"NONE": 0.6, "NAMES_METHOD": 0.2, "STATES_RESULT": 0.2}}
    assert verdict_from(split, SCOPES["prompt"], stage_filter=0.25)["verdict"] == UNCERTAIN  # 0.2 PLAN, 0.2 EXECUTE
    misread = {"choice": "NONE", "probabilities": {"NONE": 0.6, "MISREADS_ENTITY": 0.4}}
    assert verdict_from(misread, SCOPES["bootstrap"], stage_filter=0.05)["verdict"] == UNCERTAIN
    assert SCOPES["bootstrap"].stage_of["MISREADS_ENTITY"] == "OWN"


def test_the_shipped_filter_is_the_calibrated_threshold():
    """L148 calibration 2: the smallest grid value with at most 1% false halts on the Study A set is 0.55."""
    assert stage_scope.STAGE_FILTER == 0.55
    at = {"choice": "NONE", "probabilities": {"NONE": 0.45, "STATES_RESULT": 0.3, "PREVIEWS_PARTIAL": 0.25}}
    below = {"choice": "NONE", "probabilities": {"NONE": 0.5, "STATES_RESULT": 0.3, "PREVIEWS_PARTIAL": 0.2}}
    assert verdict_from(at, SCOPES["plan"])["verdict"] == CONCLUSIVE
    assert verdict_from(below, SCOPES["plan"])["verdict"] == UNCERTAIN


def test_an_answer_outside_the_categories_or_without_probabilities_is_uncertain():
    assert verdict_from({"choice": "true", "probabilities": {"true": 1.0}}, SCOPES["plan"])["verdict"] == UNCERTAIN
    assert verdict_from({"choice": "STATES_RESULT"}, SCOPES["plan"])["verdict"] == UNCERTAIN
    assert verdict_from({}, SCOPES["bootstrap"])["verdict"] == UNCERTAIN


def test_one_conclusive_artifact_makes_the_decision_conclusive():
    recipe = StageScopeRecipe([Item("interpretation", "prompt", "I"), Item("approach", "plan", "A")])
    body = {"answers": {
        "interpretation_scope": {"choice": NONE, "probabilities": _probabilities("prompt", NONE)},
        "approach_scope": {"choice": "STATES_RESULT", "probabilities": _probabilities("plan", "STATES_RESULT")}}}
    result = recipe.parse_response(body)
    assert result.verdict == CONCLUSIVE
    assert result.labels["items"]["interpretation"]["verdict"] == IN_SCOPE


# The unconfirmed route: the bootstrap analysis and both notes.

@pytest.mark.parametrize("scripted,stage", [
    ({"approach": "STATES_RESULT"}, "EXECUTE_UNCONFIRMED"),
    ({"interpretation": "NAMES_METHOD"}, "EXECUTE_UNCONFIRMED"),  # an interpretation is a prompt: no method
    ({"analysis": "ADDS_UNSTATED_FACT"}, "BOOTSTRAP_ANALYSIS"),
])
def test_a_test_run_stops_fail_closed_at_the_first_conclusive_artifact(tmp_path: Path, scripted, stage):
    engine, calls = _engine(tmp_path, Sys1(scripted), stop=True)
    response = engine.handle_user_message(REQUEST)
    events, published, deliverable = _record(tmp_path)
    assert calls == (["BOOTSTRAP_ANALYSIS"] if stage == "BOOTSTRAP_ANALYSIS"
                     else ["BOOTSTRAP_ANALYSIS", "EXECUTE_UNCONFIRMED"])  # nothing after the stop
    assert engine.controller.state.stage == Stage.CLOSED_CANCELLED
    assert engine.workspace.read_turn_status("turn_001")["status"] == "CLOSED_CANCELLED"
    assert response.closed and BODY not in response.text
    assert published["kind"] == STAGE_CONCLUSIVE_KIND and published["operation"] == stage
    assert published["decision"]["verdict"] == CONCLUSIVE
    assert BODY not in deliverable  # what a grader reads carries no deliverable
    if stage == "EXECUTE_UNCONFIRMED":
        assert published["withheld"]["body"] == BODY
    assert not any(e.get("kind") == "VERIFICATION_PASSED" for e in events)


def test_outside_a_test_run_every_stage_is_recorded_and_the_run_continues(tmp_path: Path):
    engine, _ = _engine(tmp_path, Sys1({"approach": "STATES_RESULT"}), stop=False)
    response = engine.handle_user_message(REQUEST)
    events, published, _ = _record(tmp_path)
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS
    assert BODY in response.text and published["kind"] == "RESULT"
    assert _scopes(events) == [("BOOTSTRAP_ANALYSIS", IN_SCOPE), ("EXECUTE_UNCONFIRMED", CONCLUSIVE)]


@pytest.mark.parametrize("sys1,fallback", [
    (Sys1({"approach": {c: 0.5 if c in (NONE, "STATES_RESULT") else 0.0 for c in SCOPES["plan"].choices}}),
     None),
    (Sys1(fail=True), "sys1_error:RuntimeError"),
])
def test_uncertain_or_unavailable_never_stops_a_test_run(tmp_path: Path, sys1: Sys1, fallback):
    engine, _ = _engine(tmp_path, sys1, stop=True)
    response = engine.handle_user_message(REQUEST)
    events, published, _ = _record(tmp_path)
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS
    assert published["kind"] == "RESULT" and BODY in response.text
    decisions = [e["payload"] for e in events if e.get("kind") == "STAGE_SCOPE"]
    assert decisions[-1]["fallback"] == fallback


# The confirmed route: DRAFT_PROMPT and DRAFT_PLAN.

def test_a_prompt_that_names_a_method_stops_a_test_run_at_the_prompt(tmp_path: Path):
    engine, calls = _engine(tmp_path, Sys1({"prompt": "NAMES_METHOD"}), stop=True, no_review=False)
    engine.handle_user_message(REQUEST)
    _, published, _ = _record(tmp_path)
    assert calls == ["INTERPRET_ACTIVATION", "BOOTSTRAP_ANALYSIS", "DRAFT_PROMPT"]
    assert engine.controller.state.stage == Stage.CLOSED_CANCELLED
    assert published["operation"] == "DRAFT_PROMPT" and published["withheld"]["prompt"] == PROMPT


def test_a_plan_that_names_the_answer_stops_a_test_run_at_the_plan(tmp_path: Path):
    engine, calls = _engine(tmp_path, Sys1({"plan": "STATES_RESULT"}), stop=True, no_review=False)
    engine.handle_user_message(REQUEST)
    assert engine.controller.state.stage == Stage.PROMPT_REVIEW
    response = engine.handle_user_message("/confirm")
    _, published, _ = _record(tmp_path)
    assert calls == ["INTERPRET_ACTIVATION", "BOOTSTRAP_ANALYSIS", "DRAFT_PROMPT", "DRAFT_PLAN"]
    assert engine.controller.state.stage == Stage.CLOSED_CANCELLED and response.closed
    assert published["operation"] == "DRAFT_PLAN" and published["withheld"]["plan"] == PLAN


# The A/B: the earlier stages without EXECUTE's environment and clauses.

def test_withholding_keeps_execution_context_out_of_the_earlier_stages_only(tmp_path: Path):
    def prompts(withhold: bool, root: Path) -> dict:
        requests: list = []
        engine, _ = _engine(root, Sys1(), stop=False, no_review=False, withhold=withhold, requests=requests)
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
        engine, _ = _engine(root, Sys1(), stop=False, withhold=withhold, requests=requests)
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


def test_the_settings_are_validated_and_applied():
    with pytest.raises(ValueError):
        RunSettings(stop_on_conclusive="yes")
    with pytest.raises(ValueError):
        RunSettings(withhold_execution_context=1)
    engine = SimpleNamespace()
    RunSettings(stop_on_conclusive=True, withhold_execution_context=True).apply(engine)
    assert engine.stop_on_conclusive is True and engine.withhold_execution_context is True
    defaults = RunSettings()
    assert defaults.stop_on_conclusive is False and defaults.withhold_execution_context is False


def test_the_catalogue_runner_passes_both_on_every_protocol_route(tmp_path: Path):
    def cmd(**settings):
        return run_catalogue.build_harness_command(tmp_path / "p.txt", "s", tmp_path / "t.txt", tmp_path / "d", "m",
                                                   "low", run_settings=settings)
    for route in ("unconfirmed", "confirmed"):
        parsed = repl._build_parser().parse_args(
            cmd(route=route, stop_on_conclusive=True, withhold_execution_context=True)[3:])
        assert parsed.stop_on_conclusive is True and parsed.withhold_execution_context is True
    assert "--stop-on-conclusive" not in cmd(route="unconfirmed", stop_on_conclusive=False)
    assert "--stop-on-conclusive" not in cmd(route="control", stop_on_conclusive=True)
    parsed = repl._build_parser().parse_args([])
    assert parsed.stop_on_conclusive is False and parsed.withhold_execution_context is False


# A conclusive stop halts the whole run: the catalogue runner and the study driver (the user, 2026-10-22: the
# failure is systemic, 'independent of arm').

def _result(prompt_id: str, halt: bool) -> dict:
    return {"id": prompt_id, "category": "logic_and_reasoning", "file": f"{prompt_id}.txt", "difficulty": "easy",
            "expected_routing": "PROTOCOL", "expected_stage": "CLOSED_SUCCESS", "ground_truth_status": "verified",
            "verdict": "CLOSED_CANCELLED" if halt else "CLOSED_SUCCESS", "exit_code": 1 if halt else 0,
            "timed_out": False, "elapsed_seconds": 1.0, "harness_peak_memory_mb": None, "start_time": "t",
            "session_id": "s", "transcript_file": f"results/{prompt_id}/transcript.txt", "ground_truth_check": None,
            "ground_truth_grade": {"grade": "FAIL" if halt else "PASS", "reason": "r"},
            "stage_conclusive": halt, "pdl_rules_stressed": [], "tags": [], "regression_ref": None,
            "tester_note": None}


@pytest.mark.parametrize("route", ["unconfirmed", "confirmed"])
def test_the_catalogue_run_halts_entirely_at_the_first_conclusive_stop(monkeypatch, tmp_path: Path, route):
    started = []

    def run_single_prompt(entry, *args, **kwargs):
        started.append(entry["id"])
        return _result(entry["id"], halt=True)

    monkeypatch.setattr(run_catalogue, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(run_catalogue, "code_provenance", lambda root=None: {
        "commit": "c", "dirty": False, "diff": "", "diff_sha256": None, "untracked": []})
    monkeypatch.setattr(run_catalogue, "run_single_prompt", run_single_prompt)
    monkeypatch.setattr("sys.argv", ["run_catalogue.py", "--prompt-id", "16-06,16-01", "--route", route])
    with pytest.raises(SystemExit) as stopped:
        run_catalogue.main()
    assert stopped.value.code == run_catalogue.CONCLUSIVE_HALT_EXIT
    assert len(started) == 1  # the second prompt never started
    (run_dir,) = (tmp_path / "runs").iterdir()
    meta = json.loads((run_dir / "RUN_META.json").read_text(encoding="utf-8"))
    assert meta["halted"]["after"] == 1 and meta["halted"]["of"] == 2
    assert meta["rules"]["stop_on_conclusive"] is True
    assert (run_dir / "HALTED.md").is_file()


def test_the_study_halts_entirely_and_refuses_to_resume(monkeypatch, tmp_path: Path):
    from experiments import matched_study
    from test_l145_study_tools import _config, _scripted_run

    config = _config(tmp_path)
    calls = _scripted_run(monkeypatch, config, {})
    scripted = matched_study.run_unit

    def run_unit(config, block, arm, attempt, logs):
        return {**scripted(config, block, arm, attempt, logs), "conclusive_halt": len(calls) == 2}

    monkeypatch.setattr(matched_study, "run_unit", run_unit)
    assert matched_study.cmd_run(config, type("A", (), {"max_blocks": None})()) == matched_study.CONCLUSIVE_HALT_EXIT
    assert len(calls) == 2  # nothing after the halting unit
    assert matched_study.halt_path(config).is_file()
    monkeypatch.undo()
    assert any("halted" in problem for problem in matched_study.preflight(config, check_key=False))
