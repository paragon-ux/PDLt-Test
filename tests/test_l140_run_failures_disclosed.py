"""L140: under STANDARD_EXECUTION a program that failed or was stopped is not always fed back (Tier D1 feeds back only a
program's own failures; without Tier D1 nothing is). A turn that closes anyway now says so in its provenance, instead
of only that the host "ran its programs" (run 06-06 of the L127 baseline: a program stopped by its memory limit, a
CLOSED_SUCCESS at contract_checked). Disclosure only: what closes and what the model receives are unchanged.
Offline; no model call."""
from __future__ import annotations

import json

from pdl_taskmaster.controller.mechanical_controller import Stage
from pdl_taskmaster.runtime import provenance
from pdl_taskmaster.runtime.session_engine import SessionEngine

from test_execution_phase import _run
from test_l121_mcp_flags import _recorded

FAILING = "The result.\n\n```python\nraise ValueError('the self-check failed')\n```\n"
DENIED = "The result.\n\n```python\nimport socket\nsocket.create_connection(('127.0.0.1', 9), timeout=1)\n```\n"
RUNS = "The result.\n\n```python\nprint(6 * 7)\n```\n"


def _with_tier_d1(monkeypatch):
    original = SessionEngine.__init__

    def init(self, *args, **kwargs):
        original(self, *args, **kwargs)
        self.tier_d1 = True  # as the API worker sets it (app.py)

    monkeypatch.setattr(SessionEngine, "__init__", init)


def test_a_failure_not_fed_back_is_disclosed_in_the_provenance(tmp_path):
    engine, _, executes, events = _run(tmp_path, [{"kind": "RESULT", "body": FAILING}])  # Tier D1 off
    assert engine.controller.state.stage == Stage.CLOSED_UNVERIFIED and len(executes) == 1  # unchanged: no repair
    verification = _recorded(engine)["verification"]
    assert verification["level"] == "contract_checked"
    assert verification["run_failures_not_fed_back"] == ["PROGRAM_FAILED"]
    assert verification["caveat"] == provenance.STANDARD_CAVEAT + " " + provenance.NOT_FED_BACK_CAVEAT.format(
        codes="PROGRAM_FAILED")


def test_with_tier_d1_an_environment_denial_is_disclosed_and_a_program_failure_is_repaired(tmp_path, monkeypatch):
    _with_tier_d1(monkeypatch)
    engine, _, executes, _ = _run(tmp_path / "denied", [{"kind": "RESULT", "body": DENIED}])
    assert engine.controller.state.stage == Stage.CLOSED_UNVERIFIED and len(executes) == 1
    assert _recorded(engine)["verification"]["run_failures_not_fed_back"] == ["PROGRAM_FAILED (environment denial)"]
    engine, _, executes, _ = _run(tmp_path / "failed", [{"kind": "RESULT", "body": FAILING},
                                                         {"kind": "RESULT", "body": RUNS}])
    assert engine.controller.state.stage == Stage.CLOSED_UNVERIFIED and len(executes) == 2  # fed back, then repaired
    verification = _recorded(engine)["verification"]
    assert "run_failures_not_fed_back" not in verification and verification["caveat"] == provenance.STANDARD_CAVEAT


def test_a_run_without_failures_records_nothing_new(tmp_path):
    engine, *_ = _run(tmp_path, [{"kind": "RESULT", "body": RUNS}])
    verification = _recorded(engine)["verification"]
    assert "run_failures_not_fed_back" not in verification and verification["caveat"] == provenance.STANDARD_CAVEAT


def test_the_basis_lists_the_codes_whatever_the_level():
    basis = provenance.verification_basis("CLOSED_UNVERIFIED", True, None, None, "argued_result",
                                          run_failures_not_fed_back=["WALL_CLOCK_EXCEEDED"])
    assert basis["level"] == "unverified" and basis["run_failures_not_fed_back"] == ["WALL_CLOCK_EXCEEDED"]
    assert basis["caveat"] == provenance.NOT_FED_BACK_CAVEAT.format(codes="WALL_CLOCK_EXCEEDED")
    assert json.dumps(provenance.verification_basis("CLOSED_SUCCESS", False, None, None, None)) == json.dumps(
        provenance.verification_basis("CLOSED_SUCCESS", False, None, None, None, run_failures_not_fed_back=[]))
