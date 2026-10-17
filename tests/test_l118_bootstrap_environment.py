"""L118: BOOTSTRAP_ANALYSIS receives AVAILABLE_EXECUTION_TOOLS, the declaration EXECUTE gets, so the analysis is
written knowing the environment the deliverable will run in. A fact, not guidance (ADR-0025 section 6, GUARD-01).
Offline; no model call."""
from __future__ import annotations

import json

from pdl_taskmaster.runtime.session_engine import SessionEngine

from test_unconfirmed_route import ROOT, ClassifyingSys1, _bootstrap_reply, _unconfirmed_result_reply


def test_bootstrap_receives_the_environment_declaration_execute_receives(tmp_path):
    seen = {}

    def model_call(req):
        seen[req.operation] = req.projection.document.get("operation_inputs", {}).get("AVAILABLE_EXECUTION_TOOLS")
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return _bootstrap_reply()
        if req.operation == "EXECUTE_UNCONFIRMED":
            return _unconfirmed_result_reply()
        raise AssertionError(f"unexpected operation: {req.operation}")

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=ClassifyingSys1(), no_review=True)
    engine.handle_user_message("Deduce identities of three gods A, B, and C.")
    assert seen["BOOTSTRAP_ANALYSIS"] and seen["BOOTSTRAP_ANALYSIS"] == seen["EXECUTE_UNCONFIRMED"]
    assert "third-party packages are not installed" in json.dumps(seen["BOOTSTRAP_ANALYSIS"])
