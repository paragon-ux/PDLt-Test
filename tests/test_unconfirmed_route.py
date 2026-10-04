"""Tests for the lean unconfirmed execution route (--no-review / --ultrafast, ADR-0029).

Governed by UNCONFIRMED_STANDARD.md (UNC-01 through UNC-05) and EXECUTION_CONTRACT.json.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from pdl_taskmaster.controller.mechanical_controller import Stage
from pdl_taskmaster.host.app import PDLtHost
from pdl_taskmaster.runtime.session_engine import SessionEngine

ROOT = Path(__file__).resolve().parents[1]


class ClassifyingSys1:
    """System 1 that allows every request through Phase 0 and labels its problem class."""

    is_configured = True
    model = "fake-sys1"

    def __init__(self, problem_class: str = "STANDARD_EXECUTION"):
        self.problem_class = problem_class

    def call(self, request):
        name = next(iter(request.questions))
        choice = "APPLY_PROTOCOL" if name == "route" else self.problem_class
        other = "BYPASS" if name == "route" else (
            "STANDARD_EXECUTION" if choice == "VERIFIED_EXECUTION" else "VERIFIED_EXECUTION"
        )
        return {
            "answers": {
                name: {
                    "choice": choice,
                    "confidence": 0.97,
                    "probabilities": {choice: 0.97, other: 0.03},
                }
            }
        }, 1.0


def _bootstrap_reply(task_summary: str = "Deduce identities of three gods A, B, and C.", entities: list[dict] | None = None) -> str:
    if entities is None:
        entities = [
            {"surface": "A", "kind": "identifier", "definition": None},
            {"surface": "B", "kind": "identifier", "definition": None},
            {"surface": "C", "kind": "identifier", "definition": None},
        ]
    return json.dumps({
        "kind": "ANALYSIS",
        "task_summary": task_summary,
        "approach_notes": "Evaluate question strategies.",
        "risk_notes": "",
        "task_entities": entities,
    })


def _unconfirmed_result_reply(
    body: str = "God A is True, B is Random, C is False.",
    interpretation: str = "DETERMINE identities of A, B, C",
    approach: str = "ASK god A first question",
) -> str:
    return json.dumps({
        "kind": "RESULT",
        "interpretation": interpretation,
        "approach": approach,
        "body": body,
    })


def test_standard_two_call_unconfirmed_execution(tmp_path: Path):
    """UNC-01, UNC-02, UNC-03: Two calls only (BOOTSTRAP_ANALYSIS -> EXECUTE_UNCONFIRMED)."""
    calls: list = []

    def model_call(req):
        calls.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return _bootstrap_reply()
        if req.operation == "EXECUTE_UNCONFIRMED":
            return _unconfirmed_result_reply()
        raise AssertionError(f"unexpected operation in unconfirmed route: {req.operation}")

    engine = SessionEngine(
        ROOT,
        model_call,
        workspace_root=tmp_path,
        sys1_client=ClassifyingSys1(),
        no_review=True,
    )

    response = engine.handle_user_message(
        "Three gods A, B, and C are called True, False, and Random. Determine their identities."
    )

    # Exactly two calls
    ops = [c.operation for c in calls]
    assert ops == ["BOOTSTRAP_ANALYSIS", "EXECUTE_UNCONFIRMED"]

    # Controller instance kind is UNCONFIRMED and closed with success
    assert engine.controller is not None
    assert engine.controller.state.instance_kind == "UNCONFIRMED"
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS

    # Response is closed
    assert response.closed is True
    assert response.review is None

    # Decision U3: published output presents the deliverable followed by unconfirmed working notes
    assert "God A is True, B is Random, C is False." in response.text
    assert "[unconfirmed interpretation and approach]" in response.text
    assert "Interpretation:" in response.text
    assert "Approach:" in response.text

    # Turn status in workspace
    assert engine.workspace is not None
    turn_status = engine.workspace.read_turn_status("turn_001")
    assert turn_status["status"] == "CLOSED_SUCCESS"


def test_explicit_confirm_with_pseudocode_bypasses_no_review(tmp_path: Path):
    """UNC-01: An explicit $confirm-with-pseudocode request overrides --no-review and opens confirmation instance."""
    calls: list = []

    def model_call(req):
        calls.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return _bootstrap_reply()
        if req.operation == "DRAFT_PROMPT":
            return json.dumps({
                "kind": "PROMPT",
                "prompt_body": "DETERMINE identities of A, B, C",
                "approach_handoff": "NONE",
            })
        raise AssertionError(f"unexpected operation: {req.operation}")

    engine = SessionEngine(
        ROOT,
        model_call,
        workspace_root=tmp_path,
        sys1_client=ClassifyingSys1(),
        no_review=True,
    )

    # Explicit invocation with $confirm-with-pseudocode
    response = engine.handle_user_message(
        "$confirm-with-pseudocode Three gods A, B, and C are called True, False, and Random."
    )

    # Calls BOOTSTRAP_ANALYSIS then DRAFT_PROMPT (confirmation route)
    ops = [c.operation for c in calls]
    assert ops == ["BOOTSTRAP_ANALYSIS", "DRAFT_PROMPT"]

    # Controller instance kind is CONFIRMATION and stage is PROMPT_REVIEW
    assert engine.controller is not None
    assert engine.controller.state.instance_kind == "CONFIRMATION"
    assert engine.controller.state.stage == Stage.PROMPT_REVIEW
    assert response.closed is False
    assert response.review == "prompt"


def test_request_input_transitions_to_waiting_input_and_resumes(tmp_path: Path):
    """UNC-04: REQUEST_INPUT cleanly transitions to WAITING_INPUT, subsequent input resumes unconfirmed."""
    calls: list = []
    first_execute = True

    def model_call(req):
        nonlocal first_execute
        calls.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return _bootstrap_reply()
        if req.operation == "EXECUTE_UNCONFIRMED":
            if first_execute:
                first_execute = False
                return json.dumps({
                    "kind": "REQUEST_INPUT",
                    "interpretation": "DETERMINE identities of A, B, C",
                    "approach": "ASK god A first question",
                    "body": "What does god A answer to question 1?",
                    "expected_type": "string",
                    "description": "Response from god A",
                })
            return _unconfirmed_result_reply(body="Identities determined with god A response.")
        if req.operation == "INTERPRET_EXECUTION_INPUT":
            return json.dumps({"kind": "SUPPLY_EXECUTION_INPUT"})
        raise AssertionError(f"unexpected operation: {req.operation}")

    engine = SessionEngine(
        ROOT,
        model_call,
        workspace_root=tmp_path,
        sys1_client=ClassifyingSys1(),
        no_review=True,
    )

    # Turn 1: requests input
    resp1 = engine.handle_user_message("Three gods problem...")
    assert resp1.closed is False
    assert engine.controller.state.stage == Stage.WAITING_INPUT
    assert "What does god A answer to question 1?" in resp1.text

    turn1_status = engine.workspace.read_turn_status("turn_001")
    assert turn1_status["status"] == "WAITING_INPUT"

    # Turn 2: user supplies input
    resp2 = engine.handle_user_message("God A answers 'da'")
    assert resp2.closed is True
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS
    assert "Identities determined with god A response." in resp2.text

    # Verify no DRAFT_PROMPT or DRAFT_PLAN calls occurred anywhere
    ops = [c.operation for c in calls]
    assert ops == ["BOOTSTRAP_ANALYSIS", "EXECUTE_UNCONFIRMED", "INTERPRET_EXECUTION_INPUT", "EXECUTE_UNCONFIRMED"]


def test_task_change_in_waiting_input_restarts_execution(tmp_path: Path):
    """UNC-04: Substantive task change while in WAITING_INPUT restarts unconfirmed execution with updated request."""
    calls: list = []
    first_execute = True

    def model_call(req):
        nonlocal first_execute
        calls.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return _bootstrap_reply()
        if req.operation == "EXECUTE_UNCONFIRMED":
            if first_execute:
                first_execute = False
                return json.dumps({
                    "kind": "REQUEST_INPUT",
                    "interpretation": "DETERMINE identities of A, B, C",
                    "approach": "ASK god A",
                    "body": "Waiting for input...",
                    "expected_type": "string",
                    "description": "God answer",
                })
            return _unconfirmed_result_reply(body="Different deliverable for updated task.")
        if req.operation == "INTERPRET_EXECUTION_INPUT":
            return json.dumps({"kind": "NEW_TASK"})
        raise AssertionError(f"unexpected operation: {req.operation}")

    engine = SessionEngine(
        ROOT,
        model_call,
        workspace_root=tmp_path,
        sys1_client=ClassifyingSys1(),
        no_review=True,
    )

    resp1 = engine.handle_user_message("First task...")
    assert resp1.closed is False
    assert engine.controller.state.stage == Stage.WAITING_INPUT

    # User sends a substantive change
    resp2 = engine.handle_user_message("Actually, forget the three gods, solve this completely different logic puzzle instead.")
    assert resp2.closed is True
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS
    assert "Different deliverable for updated task." in resp2.text


def test_mechanical_entity_coverage_and_lint_events_recorded(tmp_path: Path):
    """UNC-05: Task entity coverage miss and plan soundness lints on interpretation/approach are recorded as workspace events."""
    calls: list = []

    def model_call(req):
        calls.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return _bootstrap_reply(entities=[
                {"surface": "A", "kind": "identifier", "definition": None},
                {"surface": "B", "kind": "identifier", "definition": None},
                {"surface": "MISSING_ENTITY_X", "kind": "identifier", "definition": None},
            ])
        if req.operation == "EXECUTE_UNCONFIRMED":
            # interpretation does not mention MISSING_ENTITY_X, and has a plan soundness violation (invented field)
            return json.dumps({
                "kind": "RESULT",
                "interpretation": "TASK: solve for A and B only",  # "TASK:" violates PDL grammar
                "approach": "STEP 1: solve",
                "body": "Solved.",
            })
        raise AssertionError(f"unexpected operation: {req.operation}")

    engine = SessionEngine(
        ROOT,
        model_call,
        workspace_root=tmp_path,
        sys1_client=ClassifyingSys1(),
        no_review=True,
    )

    response = engine.handle_user_message("Three gods with MISSING_ENTITY_X...")
    assert response.closed is True

    # Check recorded workspace events
    events = list(engine.workspace.read_events())
    event_kinds = [e["kind"] for e in events]

    assert "TASK_ENTITY_COVERAGE_MISSING" in event_kinds
    missing_ev = next(e for e in events if e["kind"] == "TASK_ENTITY_COVERAGE_MISSING")
    assert "MISSING_ENTITY_X" in missing_ev["payload"]["entities"]
    assert missing_ev["payload"]["phase"] == "execute_unconfirmed_interpretation"

    assert "UNCONFIRMED_INTERPRETATION_LINT_FINDING" in event_kinds


def test_blocked_by_higher_priority_closes_as_refusal(tmp_path: Path):
    """ADR-0019: BLOCKED_BY_HIGHER_PRIORITY in EXECUTE_UNCONFIRMED closes with refused=True, closed=True."""
    def model_call(req):
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return _bootstrap_reply()
        if req.operation == "EXECUTE_UNCONFIRMED":
            return json.dumps({
                "kind": "BLOCKED_BY_HIGHER_PRIORITY",
                "interpretation": "DETERMINE identities of A, B, C",
                "approach": "REFUSE impossible constraint",
                "body": "Cannot solve due to policy constraint.",
            })
        raise AssertionError(f"unexpected operation: {req.operation}")

    engine = SessionEngine(
        ROOT,
        model_call,
        workspace_root=tmp_path,
        sys1_client=ClassifyingSys1(),
        no_review=True,
    )

    response = engine.handle_user_message("Solve task with forbidden constraint.")
    assert response.closed is True
    assert response.refused is True
    assert engine.controller.state.stage == Stage.CLOSED_CANCELLED


def test_host_app_no_review_wiring(tmp_path: Path):
    """PDLtHost properly configures no_review and omits $confirm-with-pseudocode wrapper."""
    class DummyWorker:
        contract_form = None

        def call(self, request):
            if request.operation == "BOOTSTRAP_ANALYSIS":
                return _bootstrap_reply()
            if request.operation == "EXECUTE_UNCONFIRMED":
                return _unconfirmed_result_reply()
            raise AssertionError(f"unexpected operation: {request.operation}")

    host = PDLtHost(
        candidate_repo=str(ROOT),
        workspace_root=str(tmp_path),
        worker=DummyWorker(),
        no_review=True,
    )

    # In no_review mode, _ensure_protocol_entry leaves raw substantive requests unwrapped
    wrapped = host._ensure_protocol_entry("Deduce identities of three gods.")
    assert not wrapped.startswith("$confirm-with-pseudocode")
    assert wrapped == "Deduce identities of three gods."

    # But an explicit review invocation is preserved
    explicit = host._ensure_protocol_entry("$confirm-with-pseudocode Deduce identities.")
    assert explicit == "$confirm-with-pseudocode Deduce identities."


def test_unconfirmed_route_with_draft_execute(tmp_path: Path):
    """When draft_execute is enabled on unconfirmed route, DRAFT_EXECUTE runs between BOOTSTRAP and EXECUTE."""
    calls = []

    def model_call(req):
        calls.append(req.operation)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return _bootstrap_reply()
        if req.operation == "DRAFT_EXECUTE":
            return json.dumps({
                "kind": "RESULT",
                "brief_body": "Use backtracking with MRV heuristic under 10M step budget.",
                "execution_entities": [],
            })
        if req.operation == "EXECUTE_UNCONFIRMED":
            inputs = req.projection.document.get("operation_inputs", {})
            req_inputs = inputs.get("REQUIRED_TASK_INPUTS", "")
            assert "EXECUTION BRIEF" in req_inputs
            assert "MRV heuristic" in req_inputs
            return _unconfirmed_result_reply()
        raise AssertionError(f"unexpected operation: {req.operation}")

    engine = SessionEngine(
        ROOT,
        model_call,
        workspace_root=tmp_path,
        sys1_client=ClassifyingSys1(),
        no_review=True,
    )
    engine.draft_execute = True

    response = engine.handle_user_message("Deduce identities of three gods A, B, and C.")
    assert response.closed is True
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS
    assert calls == ["BOOTSTRAP_ANALYSIS", "DRAFT_EXECUTE", "EXECUTE_UNCONFIRMED"]

