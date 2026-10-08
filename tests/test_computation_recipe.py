"""The computation question (L85): whether a request's deliverable is, or needs, an algorithm or a calculation.

It gates DRAFT_EXECUTE only, and only when --draft-execute is on. These tests cover the recipe, and the engine's
use of it on both routes: the brief runs for a confident yes, and for nothing else.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdl_taskmaster.controller.mechanical_controller import Stage
from pdl_taskmaster.providers.sys1.recipes.computation import COMPUTATIONAL, OTHER, ComputationRecipe
from pdl_taskmaster.runtime.session_engine import SessionEngine

ROOT = Path(__file__).resolve().parents[1]
PROMPT = "COMPUTE the answer to the stated task\nRETURN the answer"
PLAN = "DERIVE the answer\nEMIT the answer"


def _answer(choice: str, confidence: float) -> dict:
    other = OTHER if choice == COMPUTATIONAL else COMPUTATIONAL
    return {"answers": {"computation": {"choice": choice, "confidence": confidence,
                                        "probabilities": {choice: (1 + confidence) / 2, other: (1 - confidence) / 2}}}}


# ------------------------------------------------------------------ the recipe

def test_the_request_asks_one_two_way_question_about_the_request_text() -> None:
    request = ComputationRecipe().build_request({"request": "Sort these numbers."})
    assert request.state == {"request": "Sort these numbers."}
    assert list(request.questions) == ["computation"]
    question = request.questions["computation"]
    assert question.choices == [COMPUTATIONAL, OTHER]
    assert set(question.criteria) == {COMPUTATIONAL, OTHER}
    assert "symbolic parameters" in question.criteria[OTHER]  # GUARD-03.2: a formula stays standard


def test_a_confident_yes_passes_and_maps_to_computational() -> None:
    recipe = ComputationRecipe()
    result = recipe.parse_response(_answer(COMPUTATIONAL, 0.97))
    assert result.passed_gating and result.verdict == COMPUTATIONAL
    assert recipe.map_to_wire(result)["computational"] is True


@pytest.mark.parametrize("response", [
    _answer(COMPUTATIONAL, 0.60),  # below the floor
    _answer(OTHER, 0.97),  # a confident no
    {"answers": {}},  # no answer
    {"answers": {"problem_class": {"choice": "VERIFIED_EXECUTION", "confidence": 0.97,
                                   "probabilities": {"VERIFIED_EXECUTION": 0.985, "STANDARD_EXECUTION": 0.015}}}},
    {"answers": {"computation": {"choice": "VERIFIED_EXECUTION", "confidence": 0.97,
                                 "probabilities": {"VERIFIED_EXECUTION": 0.985, "STANDARD_EXECUTION": 0.015}}}},
])
def test_anything_else_is_not_a_yes(response: dict) -> None:
    recipe = ComputationRecipe()
    result = recipe.parse_response(response)
    assert not (result.passed_gating and recipe.map_to_wire(result)["computational"])


# ------------------------------------------------------------------ the engine

class Sys1:
    """Answers each question by its name and keeps the names it was asked."""

    is_configured = True
    model = "fake-sys1"

    def __init__(self, problem_class: str = "STANDARD_EXECUTION", computation: dict | Exception | None = None):
        self.problem_class = problem_class
        self.computation = computation
        self.asked: list[str] = []

    def call(self, request):
        name = next(iter(request.questions))
        self.asked.append(name)
        if name == "computation":
            if isinstance(self.computation, Exception):
                raise self.computation
            return (self.computation or _answer(OTHER, 0.97)), 1.0
        choice = "APPLY_PROTOCOL" if name == "route" else self.problem_class
        other = "BYPASS" if name == "route" else (
            "STANDARD_EXECUTION" if choice == "VERIFIED_EXECUTION" else "VERIFIED_EXECUTION")
        return {"answers": {name: {"choice": choice, "confidence": 0.97, "probabilities": {choice: 0.97, other: 0.03}}}}, 1.0


def _bootstrap() -> str:
    return json.dumps({"kind": "ANALYSIS", "task_summary": "The user states a task.", "approach_notes": "",
                       "risk_notes": "", "task_entities": []})


def _unconfirmed(tmp_path: Path, sys1: Sys1, *, draft_execute: bool = True):
    calls: list[str] = []

    def model_call(req):
        calls.append(req.operation)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return _bootstrap()
        if req.operation == "DRAFT_EXECUTE":
            return json.dumps({"kind": "RESULT", "approach": "Compute the value from the inputs.", "data_structures": [], "step_estimate": None, "invariants": [], "self_checks": [], "execution_entities": []})
        if req.operation == "EXECUTE_UNCONFIRMED":
            # A verified task needs a witness from a program; any other task closes on its text.
            body = ("```python\nimport json\nprint('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'x': 42}}))\n```"
                    if sys1.problem_class == "VERIFIED_EXECUTION" else "The result is 42.")
            return json.dumps({"kind": "RESULT", "interpretation": "DETERMINE the result", "approach": "COMPUTE it",
                               "body": body, "result_ir": {}})
        raise AssertionError(req.operation)

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=sys1, no_review=True)
    engine.draft_execute = draft_execute
    response = engine.handle_user_message("Count the subsets of 1..10 that sum to 20.")
    assert response.closed and engine.controller.state.stage == Stage.CLOSED_SUCCESS
    return calls, engine


def test_a_confident_yes_drafts_the_brief_on_the_unconfirmed_route(tmp_path) -> None:
    sys1 = Sys1(computation=_answer(COMPUTATIONAL, 0.97))
    calls, engine = _unconfirmed(tmp_path, sys1)
    assert calls == ["BOOTSTRAP_ANALYSIS", "DRAFT_EXECUTE", "EXECUTE_UNCONFIRMED"]
    assert sys1.asked.count("computation") == 1


@pytest.mark.parametrize("computation", [
    _answer(OTHER, 0.97),
    _answer(COMPUTATIONAL, 0.60),
    RuntimeError("System 1 is down"),
])
def test_no_confident_yes_means_no_brief(tmp_path, computation) -> None:
    calls, _ = _unconfirmed(tmp_path, Sys1(computation=computation))
    assert calls == ["BOOTSTRAP_ANALYSIS", "EXECUTE_UNCONFIRMED"]


def test_without_system_1_there_is_no_brief_for_a_task_that_is_not_verified(tmp_path) -> None:
    calls: list[str] = []

    def model_call(req):
        calls.append(req.operation)
        return _bootstrap() if req.operation == "BOOTSTRAP_ANALYSIS" else json.dumps(
            {"kind": "RESULT", "interpretation": "DETERMINE", "approach": "COMPUTE", "body": "42"})

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, no_review=True)
    engine.draft_execute = True
    engine.handle_user_message("Count the subsets of 1..10 that sum to 20.")
    assert calls == ["BOOTSTRAP_ANALYSIS", "EXECUTE_UNCONFIRMED"]


def test_the_question_is_not_asked_unless_the_brief_is_on(tmp_path) -> None:
    sys1 = Sys1(computation=_answer(COMPUTATIONAL, 0.97))
    calls, _ = _unconfirmed(tmp_path, sys1, draft_execute=False)
    assert calls == ["BOOTSTRAP_ANALYSIS", "EXECUTE_UNCONFIRMED"]
    assert "computation" not in sys1.asked  # Control and Arms 1 and 2 pay nothing for it


def test_a_verified_task_gets_its_brief_without_the_question(tmp_path) -> None:
    sys1 = Sys1(problem_class="VERIFIED_EXECUTION", computation=_answer(OTHER, 0.97))
    calls, _ = _unconfirmed(tmp_path, sys1)
    assert calls == ["BOOTSTRAP_ANALYSIS", "DRAFT_EXECUTE", "EXECUTE_UNCONFIRMED"]
    assert "computation" not in sys1.asked


def test_the_answer_is_recorded_as_an_event(tmp_path) -> None:
    sys1 = Sys1(computation=_answer(COMPUTATIONAL, 0.60))
    _, engine = _unconfirmed(tmp_path, sys1)
    recorded = [e["payload"] for e in engine.workspace.read_events() if e["kind"] == "COMPUTATION_CLASSIFIED"]
    assert len(recorded) == 1
    assert recorded[0]["computational"] is False and recorded[0]["fallback"] == "below_floor"
    assert recorded[0]["verdict"] == COMPUTATIONAL and recorded[0]["passed_gating"] is False


def test_the_confirmed_route_follows_the_same_gate(tmp_path) -> None:
    for computation, expected_drafts in ((_answer(COMPUTATIONAL, 0.97), 1), (_answer(OTHER, 0.97), 0)):
        calls: list[str] = []

        def model_call(req):
            calls.append(req.operation)
            if req.operation == "BOOTSTRAP_ANALYSIS":
                return _bootstrap()
            if req.operation == "DRAFT_PROMPT":
                return json.dumps({"kind": "PROMPT", "prompt_body": PROMPT, "approach_handoff": "NONE"})
            if req.operation == "DRAFT_PLAN":
                return json.dumps({"neutral_plan_body": PLAN})
            if req.operation == "DRAFT_EXECUTE":
                return json.dumps({"kind": "RESULT", "approach": "Compute the value from the inputs.", "data_structures": [], "step_estimate": None, "invariants": [], "self_checks": [], "execution_entities": []})
            return json.dumps({"kind": "RESULT", "body": "The result is 42."})

        engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path / str(expected_drafts),
                               sys1_client=Sys1(computation=computation))
        engine.draft_execute = True
        for message in ("$confirm-with-pseudocode Count the subsets of 1..10 that sum to 20.", "/confirm", "/confirm"):
            engine.handle_user_message(message)
        assert calls.count("DRAFT_EXECUTE") == expected_drafts
        assert engine.controller.state.stage == Stage.CLOSED_SUCCESS
