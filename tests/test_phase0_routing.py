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
