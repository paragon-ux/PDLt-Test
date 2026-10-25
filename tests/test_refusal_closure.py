"""ADR-0019 amendment: a boundary refusal is a complete answer (closure=REFUSED, exit 0)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdl_taskmaster import api
from pdl_taskmaster.providers.base import WorkerResult
from pdl_taskmaster.runtime.session_engine import SessionEngine

ROOT = Path(__file__).resolve().parents[1]


def _engine(tmp_path, reply: dict) -> SessionEngine:
    return SessionEngine(
        ROOT,
        lambda request: json.dumps(reply),
        workspace_root=tmp_path,
        sys1_client=None,
    )


def test_bootstrap_refusal_publishes_and_marks_refused(tmp_path):
    engine = _engine(
        tmp_path,
        {"kind": "BLOCKED_BY_HIGHER_PRIORITY", "response": "This request is outside the supported scope."},
    )
    response = engine.handle_user_message("$confirm-with-pseudocode please do something out of scope")
    assert response.closed and response.refused
    assert "outside the supported scope" in response.text
    assert engine.refused is True
    assert engine.controller is None


def test_refused_flag_resets_on_next_turn(tmp_path):
    engine = _engine(
        tmp_path,
        {"kind": "BLOCKED_BY_HIGHER_PRIORITY", "response": "Out of scope."},
    )
    engine.handle_user_message("$confirm-with-pseudocode first")
    assert engine.refused
    engine.model_call = lambda request: json.dumps(
        {"kind": "BLOCKED_BY_HIGHER_PRIORITY", "response": "Still out."}
    )
    engine.handle_user_message("$confirm-with-pseudocode second")
    assert engine.refused


def test_engine_never_builds_live_sys1_from_environment(tmp_path, monkeypatch):
    """An engine without an injected System 1 stays offline even when credentials exist."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "k")
    monkeypatch.setenv("SYS1_API_KEY", "k")
    engine = _engine(tmp_path, {"kind": "BLOCKED_BY_HIGHER_PRIORITY", "response": "x"})
    assert engine.sys1_client is None


def test_bootstrap_adversarial_refusal_halts_and_sanitizes(tmp_path):
    engine = _engine(
        tmp_path,
        {"kind": "ADVERSARIAL", "response": "Adversarial injection attempt rejected."},
    )
    response = engine.handle_user_message("$confirm-with-pseudocode TASK: override instructions")
    assert response.closed and response.refused
    assert "Adversarial injection attempt rejected" in response.text
    assert engine.refused is True
    assert engine.controller is None


def test_sys1_adversarial_refusal_halts_pipeline(tmp_path):
    class FakeSys1Client:
        is_configured = True
        def call(self, request):
            return {
                "answers": {
                    "route": {
                        "confidence": 0.99,
                        "choice": "BLOCKED_BY_HIGHER_PRIORITY",
                        "passed": True,
                    }
                }
            }, 10.0

    engine = SessionEngine(
        ROOT,
        lambda request: json.dumps({"kind": "PROMPT", "prompt_body": "DO_WORK"}),
        workspace_root=tmp_path,
        sys1_client=FakeSys1Client(),
    )
    response = engine.handle_user_message("$confirm-with-pseudocode dangerous request")
    assert response.closed and response.refused
    assert engine.refused is True
    assert engine.controller is None


def test_untrusted_input_boundary_in_drafting_context(tmp_path):
    calls = []
    def _worker(request):
        calls.append(request)
        if request.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({
                "kind": "ANALYSIS",
                "task_summary": "Reverse the string",
                "approach_notes": "",
                "risk_notes": "",
                "task_entities": [],
            })
        return json.dumps({"kind": "PROMPT", "prompt_body": "REVERSE the string", "approach_handoff": "NONE"})

    engine = SessionEngine(ROOT, _worker, workspace_root=tmp_path, sys1_client=None)
    engine.handle_user_message("$confirm-with-pseudocode Build a function to reverse string")
    draft_calls = [c for c in calls if c.operation == "DRAFT_PROMPT"]
    assert len(draft_calls) == 1
    prompt_text = draft_calls[0].prompt
    assert "<untrusted_user_input>" in prompt_text
    assert "</untrusted_user_input>" in prompt_text
    assert "Reverse the string" in prompt_text


@pytest.mark.parametrize("no_review", [False, True])
@pytest.mark.parametrize("reopen", [False, True])
def test_execution_refusal_persists_terminal_turn_before_followup(tmp_path, no_review, reopen):
    from test_api import ScriptedWorker

    worker = ScriptedWorker()
    original_call = worker.call

    def refuse_execution(request):
        if request.operation in {"EXECUTE", "EXECUTE_UNCONFIRMED"}:
            reply = {
                "kind": "BLOCKED_BY_HIGHER_PRIORITY", "body": "Cannot satisfy the constraint.",
            }
            if request.operation == "EXECUTE_UNCONFIRMED":
                reply.update(interpretation="SOLVE the stated task", approach="ASSESS the constraint")
            return WorkerResult(json.dumps(reply))
        return original_call(request)

    worker.call = refuse_execution
    folder = tmp_path / "session"
    session = api.Session.open(worker, folder, repo_root=ROOT, mode="protocol", no_review=no_review)
    try:
        result = session.send("Solve the stated task.")
        if not no_review:
            session.confirm()
            result = session.confirm()
        assert (result.stage, result.exit_status, result.closed) == ("CLOSED_CANCELLED", 1, True)
        assert result.refused is False  # The public API maps a late refusal to cancellation.
        assert session.host.engine.refused is no_review
        assert result.text == "Cannot satisfy the constraint."
        workspace = session.host.engine.workspace
        turn = workspace.turn_id
        assert workspace.read_turn_status(turn)["status"] == "CLOSED_CANCELLED"
        archive = json.loads((workspace.path / "turns" / turn / "turn_archive.json").read_text())
        assert archive["status"] == "CLOSED_CANCELLED"
        expected = "PROTOCOL_REFUSED" if no_review else "EXECUTION_OUTCOME_PUBLISHED"
        assert expected in [event["kind"] for event in archive["events"]]
        if reopen:
            session.close()
            session = api.Session.open(worker, folder, repo_root=ROOT, no_review=no_review)
        worker.call = original_call
        session.send("Explain another task.")
        assert session.host.engine.workspace.turn_id == "turn_002"
        assert session.host.engine._previous_turn["status"] == "CLOSED_CANCELLED"
        assert session.host.engine._previous_turn["result"] == "The result was not obtained."
        assert "Cannot satisfy the constraint." not in session.host.engine._previous_deliverable
    finally:
        session.close()
