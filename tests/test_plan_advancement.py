"""PLAN-02 gate: a response plan that restates the confirmed prompt is rejected at
plan review, and a plan that exposes an approach passes, even when it reuses the
prompt's concepts.

System 1 is scripted here, so these tests fix what the harness does with each
verdict (redraft, host note, no advance confirmation). Whether the live System 1
judges real plans correctly is measured by the logic-and-reasoning catalogue's
plan-gate cases (prompts/16_logic_and_reasoning/plan_gate_cases.json,
run_plan_gate.py).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdl_taskmaster.providers.sys1.recipes.plan_advancement import CHECKS, PROMPT_STATES_METHOD, PlanAdvancementRecipe
from pdl_taskmaster.runtime.session_engine import SessionEngine

ROOT = Path(__file__).resolve().parents[1]

THREE_GODS = (
    "Three gods A, B, and C are called, in no particular order, True, False, and Random. True always speaks "
    "truly, False always speaks falsely, but whether Random speaks truly or falsely is a completely random "
    "matter. Your task is to determine the identities of A, B, and C by asking three yes-no questions; each "
    "question must be put to exactly one god. The gods understand English, but will answer all questions in "
    "their own language, in which the words for yes and no are da and ja, in some order. You do not know which "
    "word means which."
)

# The prompt pseudocode and the copied response plan from the live session.
GODS_PROMPT = (
    'ASK a yes-no question in English to god A, receiving an answer of either "da" or "ja". RECORD the answer.\n'
    'ASK a yes-no question in English to god B, receiving an answer of either "da" or "ja". RECORD the answer.\n'
    'ASK a yes-no question in English to god C, receiving an answer of either "da" or "ja". RECORD the answer.\n'
    'NOTE that the words "da" and "ja" correspond to yes and no, but the mapping is unknown.\n'
    "DEDUCE the identities of gods A, B, and C (each being True, False, or Random, in some order) using the "
    'three recorded answers, the known behavior of each god type, and the unknown "da"/"ja" mapping.\n'
    "OUTPUT the identity of each god (A, B, C) indicating which is the True god, which is the False god, and "
    "which is the Random god."
)

COPIED_PLAN = (
    'ASK a yes-no question in English to god A and RECEIVE an answer of "da" or "ja".\n'
    "RECORD the answer from god A.\n"
    'ASK a yes-no question in English to god B and RECEIVE an answer of "da" or "ja".\n'
    "RECORD the answer from god B.\n"
    'ASK a yes-no question in English to god C and RECEIVE an answer of "da" or "ja".\n'
    "RECORD the answer from god C.\n"
    'NOTE that the words "da" and "ja" correspond to yes and no, but the mapping is unknown.\n'
    'DEDUCE the identities of gods A, B, and C (True, False, Random) using the three recorded answers, the known '
    'behavior of each god type, and the unknown "da"/"ja" mapping.\n'
    "OUTPUT the identity of each god, indicating which is the True god, which is the False god, and which is the "
    "Random god."
)

# Same concepts (gods, da/ja, True/False/Random), but it says how: no final identities (PLAN-04).
REASONING_PLAN = (
    "FRAME every question as a question about what the asked god would answer to an inner question, so that the "
    "reply means the same whether the god lies and whichever word means yes\n"
    "USE the first question, put to A, to single out one of B and C that cannot be Random\n"
    "ASK that god the second question to learn whether it is True or False\n"
    "ASK the same god the third question to learn which of the other two is Random\n"
    "ASSIGN the remaining identity by elimination"
)

VERDICTS = {
    "fail": {**{c: ("false", 0.95) for c in CHECKS}, PROMPT_STATES_METHOD: ("false", 0.95)},
    "pass": {**{c: ("true", 0.95) for c in CHECKS}, PROMPT_STATES_METHOD: ("false", 0.95)},
    "unsure": {**{c: ("true", 0.55) for c in CHECKS}, PROMPT_STATES_METHOD: ("false", 0.95)},
    # The prompt already says how; a plan that only follows it has no new procedural steps to add.
    "prompt_has_method": {
        **{c: ("false", 0.95) for c in ("solution_actions", "constraints_addressed", "advances")},
        **{c: ("true", 0.95) for c in ("no_evasion", "no_answer_leakage")},
        PROMPT_STATES_METHOD: ("true", 0.95),
    },
}


class Judge:
    """System 1 stand-in. Routing questions pass; plan-advancement questions get the
    verdict scripted for the plan under review (by exact plan text)."""

    is_configured, model = True, "fake-sys1"

    def __init__(self, verdicts: dict[str, str], *, prose: str = ""):
        self.verdicts = verdicts
        self.prose = prose  # decision prose that must never reach the drafting model
        self.plans_judged: list[str] = []

    def call(self, request):
        names = list(request.questions)
        if names[0] in (*CHECKS, PROMPT_STATES_METHOD):
            plan = request.state["response_plan"]
            self.plans_judged.append(plan)
            answers = VERDICTS[self.verdicts[plan]]
            return {
                "answers": {
                    name: {"choice": answers[name][0], "confidence": answers[name][1],
                           "probabilities": {answers[name][0]: answers[name][1],
                                             "true" if answers[name][0] == "false" else "false": 1 - answers[name][1]}}
                    for name in names
                },
                "metadata": {"rationale": self.prose},
            }, 1.0
        name = names[0]
        choice = {"route": "APPLY_PROTOCOL", "problem_class": "STANDARD_EXECUTION"}.get(name, "UNSET")
        confidence = 0.97 if choice != "UNSET" else 0.3
        return {"answers": {name: {"choice": choice, "confidence": confidence,
                                   "probabilities": {choice: confidence}}}}, 1.0


class Worker:
    """System 2 stand-in: per-operation replies; a list is consumed in order."""

    def __init__(self, plans: list[str]):
        self.replies = {
            "BOOTSTRAP_ANALYSIS": [{"kind": "ANALYSIS", "task_summary": THREE_GODS, "approach_notes": "",
                                    "risk_notes": "", "task_entities": []}],
            "DRAFT_PROMPT": [{"kind": "PROMPT", "prompt_body": GODS_PROMPT, "approach_handoff": "NONE"}],
            "DRAFT_PLAN": [{"neutral_plan_body": plan} for plan in plans],
            "REVISE_PLAN": [{"neutral_plan_body": plan} for plan in plans],
            "EXECUTE": [{"kind": "RESULT", "body": "A is True, B is Random, C is False."}],
        }
        self.requests: list = []

    def __call__(self, request):
        self.requests.append(request)
        replies = self.replies[request.operation]
        reply = replies.pop(0) if len(replies) > 1 else replies[0]
        return json.dumps(reply)

    def calls(self, operation: str) -> list:
        return [r for r in self.requests if r.operation == operation]


def _events(engine: SessionEngine, kind: str) -> list[dict]:
    return [e for e in engine.workspace.read_events() if e["kind"] == kind]


def _to_plan_review(tmp_path, worker, judge):
    engine = SessionEngine(ROOT, worker, workspace_root=tmp_path, sys1_client=judge)
    engine.handle_user_message("$confirm-with-pseudocode " + THREE_GODS)
    return engine, engine.handle_user_message("/confirm")  # accept the prompt: the plan is drafted


def test_copied_plan_is_rejected_at_plan_review(tmp_path):
    """The live failure: the plan copied the prompt's structure, passed review and
    the execution then declared the puzzle unsolvable."""
    judge = Judge({COPIED_PLAN: "fail"})
    worker = Worker([COPIED_PLAN, COPIED_PLAN])
    engine, response = _to_plan_review(tmp_path, worker, judge)

    assert len(worker.calls("DRAFT_PLAN")) == 2  # one redraft carrying the finding
    assert response.review == "plan" and response.host_findings  # never confirmed in advance
    assert "[host] PLAN-02: this plan restates the prompt" in response.text
    assert engine.controller.state.current_plan.body == COPIED_PLAN  # no host rewrite (AUTH-05)
    assert engine.controller.state.stage.value == "PLAN_REVIEW"
    assert not worker.calls("EXECUTE")
    (retry,) = _events(engine, "PLAN_ADVANCEMENT_RETRY")
    assert retry["payload"]["failed_checks"] == list(CHECKS)
    (unresolved,) = _events(engine, "PLAN_ADVANCEMENT_UNRESOLVED")
    assert unresolved["payload"]["host_note"] is True


def test_redraft_carries_only_the_failed_checks(tmp_path):
    """The correction names which checks failed and nothing about how to solve the task."""
    judge = Judge({COPIED_PLAN: "fail"}, prose="ask each god what the other would say")
    worker = Worker([COPIED_PLAN, COPIED_PLAN])
    _to_plan_review(tmp_path, worker, judge)

    first, redraft = worker.calls("DRAFT_PLAN")
    assert "OPERATOR CORRECTION" not in first.prompt
    assert "PLAN-02, minimum sufficient procedure" in redraft.prompt
    assert "do not state the result itself (PLAN-04)" in redraft.prompt
    assert "what the other would say" not in redraft.prompt  # decision prose never reaches System 2


def test_redraft_that_exposes_the_approach_passes(tmp_path):
    judge = Judge({COPIED_PLAN: "fail", REASONING_PLAN: "pass"})
    worker = Worker([COPIED_PLAN, REASONING_PLAN])
    engine, response = _to_plan_review(tmp_path, worker, judge)

    assert judge.plans_judged == [COPIED_PLAN, REASONING_PLAN]
    assert response.review == "plan" and not response.host_findings
    assert "[host]" not in response.text
    assert engine.controller.state.current_plan.body == REASONING_PLAN
    assert not _events(engine, "PLAN_ADVANCEMENT_UNRESOLVED")


def test_reasoning_plan_passes_although_it_reuses_the_prompt_concepts(tmp_path):
    """Substantive advancement, not textual difference: the plan names the same gods,
    words and identities as the prompt, and is accepted on the first draft."""
    judge = Judge({REASONING_PLAN: "pass"})
    worker = Worker([REASONING_PLAN])
    engine, response = _to_plan_review(tmp_path, worker, judge)

    assert len(worker.calls("DRAFT_PLAN")) == 1
    assert response.review == "plan" and not response.host_findings
    (event,) = _events(engine, "PLAN_ADVANCEMENT")
    assert event["payload"]["verdict"] == "ADVANCES" and event["payload"]["failed_checks"] == []


def test_uncertain_judgment_does_not_flag_the_plan(tmp_path):
    judge = Judge({COPIED_PLAN: "unsure"})
    worker = Worker([COPIED_PLAN])
    engine, response = _to_plan_review(tmp_path, worker, judge)

    assert len(worker.calls("DRAFT_PLAN")) == 1 and not response.host_findings
    (event,) = _events(engine, "PLAN_ADVANCEMENT")
    assert event["payload"]["verdict"] == "UNCERTAIN" and event["payload"]["fallback"] == "below_floor"


def test_without_system1_the_gate_records_that_it_did_not_run(tmp_path):
    worker = Worker([COPIED_PLAN])
    engine = SessionEngine(ROOT, worker, workspace_root=tmp_path, sys1_client=None)
    engine.handle_user_message("$confirm-with-pseudocode " + THREE_GODS)
    response = engine.handle_user_message("/confirm")
    assert not response.host_findings
    (event,) = _events(engine, "PLAN_ADVANCEMENT")
    assert event["payload"]["verdict"] is None and event["payload"]["fallback"] == "sys1_unavailable"


def test_revised_plan_is_checked_too(tmp_path):
    judge = Judge({REASONING_PLAN: "pass", COPIED_PLAN: "fail"})
    worker = Worker([REASONING_PLAN])
    engine, _ = _to_plan_review(tmp_path, worker, judge)
    worker.replies["REVISE_PLAN"] = [{"neutral_plan_body": COPIED_PLAN}]
    response = engine.handle_user_message("/revise keep it shorter")
    assert response.review == "plan" and response.host_findings
    assert [e["payload"]["operation"] for e in _events(engine, "PLAN_ADVANCEMENT_UNRESOLVED")] == ["REVISE_PLAN"]


@pytest.mark.parametrize(
    "answers, verdict, failed",
    [
        ({c: ("true", 0.95) for c in CHECKS}, "ADVANCES", []),
        ({**{c: ("true", 0.95) for c in CHECKS}, "constraints_addressed": ("false", 0.9)}, "RESTATES",
         ["constraints_addressed"]),
        ({**{c: ("true", 0.5) for c in CHECKS}, "advances": ("false", 0.9)}, "RESTATES", ["advances"]),
        ({c: ("true", 0.5) for c in CHECKS}, "UNCERTAIN", []),
        ({c: ("maybe", 0.99) for c in CHECKS}, "UNCERTAIN", []),
    ],
)
def test_recipe_verdicts(answers, verdict, failed):
    """One confident failure is enough to reject; passing needs every check confident."""
    body = {"answers": {k: {"choice": c, "confidence": p, "probabilities": {c: p}} for k, (c, p) in answers.items()}}
    wire = PlanAdvancementRecipe().map_to_wire(PlanAdvancementRecipe().parse_response(body))
    assert wire["verdict"] == verdict and wire["failed_checks"] == failed


def test_recipe_sees_only_the_prompt_and_the_plan():
    request = PlanAdvancementRecipe().build_request(
        {"confirmed_prompt": GODS_PROMPT, "response_plan": COPIED_PLAN, "request": THREE_GODS}
    )
    assert request.state == {"confirmed_prompt": GODS_PROMPT, "response_plan": COPIED_PLAN}
    assert list(request.questions) == [*CHECKS, PROMPT_STATES_METHOD]


def test_plan_is_not_rejected_when_the_prompt_already_states_the_method(tmp_path):
    """Live 16-02: the prompt pseudocode itself carried the whole resolution, so no plan
    could add a step; rejecting it only cost a redraft that could not do better."""
    judge = Judge({COPIED_PLAN: "prompt_has_method"})
    worker = Worker([COPIED_PLAN])
    engine, response = _to_plan_review(tmp_path, worker, judge)
    assert len(worker.calls("DRAFT_PLAN")) == 1 and not response.host_findings
    (event,) = _events(engine, "PLAN_ADVANCEMENT")
    assert event["payload"]["verdict"] == "PROMPT_STATES_METHOD" and event["payload"]["prompt_states_method"] is True
