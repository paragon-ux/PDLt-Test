"""ADR-0019 amendment: a boundary refusal is a complete answer (closure=REFUSED, exit 0)."""
from __future__ import annotations

import json
from pathlib import Path

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
