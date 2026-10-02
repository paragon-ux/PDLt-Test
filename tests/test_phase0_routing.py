"""Phase 0: System 1 routes the request over environment recipe state, before System 2."""
from __future__ import annotations

import json
from pathlib import Path

from pdl_taskmaster.runtime.session_engine import SessionEngine

ROOT = Path(__file__).resolve().parents[1]
CUTOFF = "2031-02"


class FakeSys1:
    """Stands in for the System 1 decisions backend."""

    is_configured = True
    model = "fake-sys1"

    def __init__(self, route_choice: str = "APPLY_PROTOCOL", confidence: float = 0.97, boom: bool = False):
        self.route_choice = route_choice
        self.confidence = confidence
        self.boom = boom
        self.requests: list = []

    def call(self, request):
        self.requests.append(request)
        if self.boom:
            raise RuntimeError("sys1 down")
        name = next(iter(request.questions))
        if name == "route":
            other = "APPLY_PROTOCOL" if self.route_choice != "APPLY_PROTOCOL" else "BLOCKED_BY_HIGHER_PRIORITY"
            answer = {
                "choice": self.route_choice,
                "confidence": self.confidence,
                "probabilities": {self.route_choice: self.confidence, other: round(1 - self.confidence, 4)},
            }
        else:  # problem_class and anything else
            answer = {
                "choice": "STANDARD_EXECUTION",
                "confidence": 0.97,
                "probabilities": {"STANDARD_EXECUTION": 0.97, "VERIFIED_EXECUTION": 0.03},
            }
        return {"answers": {name: answer}}, 1.0


def _engine(tmp_path, sys1, s2_calls: list, monkeypatch):
    monkeypatch.setenv("PDLT_KNOWLEDGE_CUTOFF", CUTOFF)

    def model_call(request):
        s2_calls.append(request)
        # Bootstrap block keeps the run short if System 2 is (unexpectedly) reached.
        return json.dumps({"kind": "BLOCKED_BY_HIGHER_PRIORITY", "response": "stop"})

    return SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=sys1)


def test_gated_block_refuses_without_touching_system2(tmp_path, monkeypatch):
    sys1, s2_calls = FakeSys1(route_choice="BLOCKED_BY_HIGHER_PRIORITY"), []
    engine = _engine(tmp_path, sys1, s2_calls, monkeypatch)
    response = engine.handle_user_message("$confirm-with-pseudocode any request text")
    assert response.closed and response.refused and engine.refused
    assert s2_calls == []
    assert engine.controller is None
    state = sys1.requests[0].state
    assert state["knowledge_cutoff"] == CUTOFF
    assert state["policy_scope"] and state["sandbox_network"]


def test_environment_settings_never_reach_system2(tmp_path, monkeypatch):
    sys1, s2_calls = FakeSys1(route_choice="APPLY_PROTOCOL"), []
    engine = _engine(tmp_path, sys1, s2_calls, monkeypatch)
    engine.handle_user_message("$confirm-with-pseudocode any request text")
    assert s2_calls, "System 2 should run when System 1 routes APPLY_PROTOCOL"
    for request in s2_calls:
        assert CUTOFF not in request.prompt
        assert "knowledge_cutoff" not in request.prompt


def test_low_confidence_block_does_not_refuse(tmp_path, monkeypatch):
    sys1, s2_calls = FakeSys1(route_choice="BLOCKED_BY_HIGHER_PRIORITY", confidence=0.55), []
    engine = _engine(tmp_path, sys1, s2_calls, monkeypatch)
    engine.handle_user_message("$confirm-with-pseudocode any request text")
    assert s2_calls, "no gated System 1 evidence means the protocol proceeds"


def test_sys1_failure_or_absence_does_not_refuse(tmp_path, monkeypatch):
    for sys1 in (FakeSys1(boom=True), None):
        s2_calls: list = []
        engine = _engine(tmp_path / ("a" if sys1 else "b"), sys1, s2_calls, monkeypatch)
        engine.handle_user_message("$confirm-with-pseudocode any request text")
        assert s2_calls


def test_refusal_states_the_configured_boundaries(tmp_path, monkeypatch):
    sys1, s2_calls = FakeSys1(route_choice="BLOCKED_BY_HIGHER_PRIORITY"), []
    engine = _engine(tmp_path, sys1, s2_calls, monkeypatch)
    response = engine.handle_user_message("$confirm-with-pseudocode any request text")
    assert response.refused
    assert CUTOFF in response.text and "network access disabled" in response.text
    assert "policy scope 'technical'" in response.text


def test_gated_bypass_answers_directly_for_explicit_invocations(tmp_path, monkeypatch):
    """TARGET_ARCHITECTURE §3: BYPASS goes to a direct answer even when the host
    prefixed the message with the explicit invocation; no instance is opened."""
    sys1, s2_calls = FakeSys1(route_choice="BYPASS"), []
    engine = _engine(tmp_path, sys1, s2_calls, monkeypatch)
    response = engine.handle_user_message("$confirm-with-pseudocode hello")
    assert response.bypass and response.text is None and not response.closed
    assert s2_calls == [] and engine.controller is None
    assert any(e["kind"] == "DIRECT_ANSWER_ROUTED" for e in engine.workspace._events)


def test_gated_protocol_discussion_answers_directly_for_explicit_invocations(tmp_path, monkeypatch):
    sys1, s2_calls = FakeSys1(route_choice="PROTOCOL_DISCUSSION"), []
    monkeypatch.setenv("PDLT_KNOWLEDGE_CUTOFF", CUTOFF)

    def model_call(request):
        s2_calls.append(request)
        return json.dumps({"body": "The protocol drafts a prompt, then a plan."})

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=sys1)
    response = engine.handle_user_message("$confirm-with-pseudocode how does this protocol work?")
    assert [c.operation for c in s2_calls] == ["ANSWER_PROTOCOL_DISCUSSION"]
    assert response.bypass and engine.controller is None


def test_ungated_bypass_keeps_the_explicit_invocation(tmp_path, monkeypatch):
    sys1, s2_calls = FakeSys1(route_choice="BYPASS", confidence=0.6), []
    engine = _engine(tmp_path, sys1, s2_calls, monkeypatch)
    engine.handle_user_message("$confirm-with-pseudocode hello")
    assert s2_calls and s2_calls[0].operation == "BOOTSTRAP_ANALYSIS"


def test_direct_reply_is_presented_as_text_with_the_execution_environment(tmp_path, monkeypatch):
    """Session log: bypass replies printed raw JSON ({"message": "Hello! ..."}) and
    claimed "I cannot execute code" in a session whose sandbox runs Python."""
    from pdl_taskmaster.host.app import PDLtHost
    from pdl_taskmaster.providers.base import WorkerResult

    monkeypatch.setenv("PDLT_KNOWLEDGE_CUTOFF", CUTOFF)

    class BypassWorker:
        sys1_client = FakeSys1(route_choice="BYPASS")
        requests: list = []

        def call(self, request):
            self.requests.append(request)
            return WorkerResult('{"message": "Hello! How can I assist you today?"}')

    worker = BypassWorker()
    host = PDLtHost(ROOT, worker=worker, workspace_root=tmp_path / "ws", run_id="bypass").start()
    try:
        turn = host.handle("hi")
    finally:
        host.close()
    assert turn.bypass and turn.text == "Hello! How can I assist you today?"
    (request,) = worker.requests
    assert request.operation == "BYPASS_ORDINARY" and request.prompt == "hi"
    environment = host.engine.sandbox.decision_state()["execution_environment"]
    assert request.environment.startswith(environment)
    assert "Programs run only in the execution stage of a confirmed task" in request.environment


def test_plain_reply_text_unwraps_only_a_single_string():
    from pdl_taskmaster.host.app import _plain_reply_text

    assert _plain_reply_text('{"response": "Yes, I\'m here."}') == "Yes, I'm here."
    assert _plain_reply_text("Plain answer.") == "Plain answer."
    assert _plain_reply_text('{"a": "x", "b": "y"}') == '{"a": "x", "b": "y"}'
    assert _plain_reply_text('{"count": 3}') == '{"count": 3}'


def test_api_worker_sends_a_direct_reply_as_plain_text(monkeypatch):
    from pdl_taskmaster.host.app import _PlainRequest
    from pdl_taskmaster.providers.api_worker import ApiWorker

    sent = {}

    def fake_send(self, req, deadline=None):
        sent.update(json.loads(req.data))
        return {"status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": "Hello."}]}]}

    monkeypatch.setattr(ApiWorker, "_send_json_with_retries", fake_send)
    monkeypatch.setattr(ApiWorker, "_resolve_api_key", lambda self: "k")
    result = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT).call(
        _PlainRequest("hi", environment="Python 3.12 interpreter; network access is disabled."))
    assert result.text == "Hello."
    assert sent["input"] == "hi" and "JSON" not in sent["input"]
    assert sent["instructions"] == ("Execution environment of this session (host fact): "
                                    "Python 3.12 interpreter; network access is disabled.")
    assert "text" not in sent
