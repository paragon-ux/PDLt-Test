"""L164 (ADR-0019 amendment): exit 0 means host-verified on every protocol route. A published result the host checked
only against its contract closes CLOSED_UNVERIFIED (exit 5) with the reason contract_checked, and its provenance keeps
the level contract_checked and its caveat; a result the host reproduced still closes CLOSED_SUCCESS. Offline."""
from __future__ import annotations

import json

import pytest

from pdl_taskmaster.api.outcome import exit_status
from pdl_taskmaster.controller.mechanical_controller import Stage
from pdl_taskmaster.runtime import provenance

from test_agent_tools import _engine, outcome
from test_execution_phase import ROOT, _ir, _run
from test_l116_closure import POSITIVE, _unverified_reasons


def _closure(engine, events):
    record = engine.workspace.read_provenance()
    return engine.controller.state.stage, _unverified_reasons(events), record["verification"]


def test_a_contract_checked_confirmed_result_closes_unverified(tmp_path):
    engine, _, _, events = _run(tmp_path, [{"kind": "RESULT", "body": "The answer is 42.", "result_ir": _ir()}])
    stage, reasons, verification = _closure(engine, events)
    assert (stage, reasons) == (Stage.CLOSED_UNVERIFIED, [provenance.CONTRACT_ONLY])
    assert verification["level"] == "contract_checked" and verification["caveat"] == provenance.STANDARD_CAVEAT
    assert verification["unverified_reason"] == provenance.CONTRACT_ONLY
    assert exit_status(stage.value) == 5


def test_a_contract_checked_unconfirmed_result_closes_unverified(tmp_path):
    engine, response, _, events = _engine(tmp_path, lambda req: json.dumps(outcome("The answer is 42.")),
                                          agent_tools_on=False, problem_class="STANDARD_EXECUTION")
    stage, reasons, verification = _closure(engine, events)
    assert response.closed and (stage, reasons) == (Stage.CLOSED_UNVERIFIED, [provenance.CONTRACT_ONLY])
    assert verification["level"] == "contract_checked"


def test_a_reproduced_result_still_closes_success(tmp_path):
    engine, _, _, events = _run(tmp_path, [{"kind": "RESULT", "body": POSITIVE, "result_ir": _ir()}],
                                problem_class="VERIFIED_EXECUTION")
    stage, reasons, verification = _closure(engine, events)
    assert (stage, reasons, verification["level"]) == (Stage.CLOSED_SUCCESS, [], "host_verified")


@pytest.mark.parametrize("status, reason, level", [
    ("CLOSED_UNVERIFIED", provenance.CONTRACT_ONLY, "contract_checked"),
    ("CLOSED_UNVERIFIED", "argued_result", "unverified"),
    ("CLOSED_SUCCESS", None, "contract_checked"),  # a turn closed before L164 reads as it was recorded
])
def test_the_level_follows_the_reason(status, reason, level):
    assert provenance.verification_basis(status, False, None, None, reason)["level"] == level


def test_no_standard_prompt_expects_closed_success():
    for name in ("CATALOGUE_MANIFEST.jsonl", "TARGETED_MANIFEST.jsonl"):
        rows = [json.loads(line) for line in (ROOT / "prompts" / name).read_text(encoding="utf-8").splitlines()
                if line.strip()]
        assert not [r["id"] for r in rows
                    if r["expected_routing"] == "STANDARD_EXECUTION" and r["expected_stage"] == "CLOSED_SUCCESS"]
