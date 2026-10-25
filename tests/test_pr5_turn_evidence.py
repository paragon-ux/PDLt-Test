"""F3: mixed public-session turns cannot publish previous-turn execution evidence. Offline."""
import hashlib
import json
from pathlib import Path

import pytest

from pdl_taskmaster import api
from pdl_taskmaster.providers.base import WorkerResult
from pdl_taskmaster.verification.sandbox import SandboxResult

from test_agent_tools import GOOD, outcome
from test_api import ROOT
from test_computation_recipe import _bootstrap
from test_l153_modes import DirectWorker


class MixedWorker(DirectWorker):
    def call(self, request):
        if request.operation == "BOOTSTRAP_ANALYSIS":
            return WorkerResult(_bootstrap())
        if request.operation == "EXECUTE_UNCONFIRMED":
            return WorkerResult(json.dumps(outcome(GOOD)))
        return super().call(request)


def _recorded_sandbox(*args, **kwargs):
    # Recorded-shape response tests host ownership, without executing a model program.
    return SandboxResult('WITNESS: {"polarity":"positive","data":{"x":42}}\n', "", 0, 1, steps_used=10)


def _assert_direct_evidence(result):
    assert result.stage == "CLOSED_UNVERIFIED" and result.exit_status == 5
    evidence = result.provenance["verification"]
    assert evidence["level"] == "unverified" and evidence["unverified_reason"] == "direct_answer"
    assert evidence["witness_form"] == "none" and evidence["reproduced_by_host"] is False
    assert "checker" not in evidence and "run_failures_not_fed_back" not in evidence
    assert result.provenance["deliverable_sha256"] == hashlib.sha256(result.text.encode()).hexdigest()


def test_verified_saver_turn_then_direct_has_only_its_own_evidence(tmp_path, monkeypatch):
    worker = MixedWorker(problem_class="VERIFIED_EXECUTION")
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode="saver") as session:
        monkeypatch.setattr(session.host.engine.sandbox, "run_code", _recorded_sandbox)
        first = session.send("Compute 6 times 7.")
        assert first.provenance["verification"]["reproduced_by_host"] is True
        worker.sys1_client.problem_class = "STANDARD_EXECUTION"
        second = session.send("Explain the result in one sentence.")
        _assert_direct_evidence(second)
        assert not any(e["kind"] == "SANDBOX_RUN" for e in session.host.engine.workspace.read_events())
        workspace = Path(session.status()["workspace_path"])
    programs = list(workspace.rglob("program-output.json"))
    assert len(programs) == 1 and "turn_001" in programs[0].parts
    assert first.provenance["deliverable_sha256"] != second.provenance["deliverable_sha256"]


def test_direct_to_direct_then_verified_does_not_reuse_a_direct_reason(tmp_path, monkeypatch):
    worker = MixedWorker()
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode="saver") as session:
        _assert_direct_evidence(session.send("Explain one idea."))
        _assert_direct_evidence(session.send("Explain a second idea."))
        worker.sys1_client.problem_class = "VERIFIED_EXECUTION"
        monkeypatch.setattr(session.host.engine.sandbox, "run_code", _recorded_sandbox)
        verified = session.send("Compute 6 times 7.")
        assert verified.stage == "CLOSED_SUCCESS" and verified.exit_status == 0
        assert verified.provenance["verification"]["level"] == "host_verified"


@pytest.mark.parametrize("failed", [False, True])
def test_refused_or_cancelled_turn_does_not_contaminate_next_answer(tmp_path, monkeypatch, failed):
    worker = MixedWorker(problem_class="VERIFIED_EXECUTION", p_poisoned=0.02 if failed else 0.97)
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode="saver") as session:
        monkeypatch.setattr(session.host.engine.sandbox, "run_code",
                            lambda *a, **k: SandboxResult("", "failed", 1, 1, steps_used=1))
        session.host.engine.max_repairs = 0
        first = session.send("Compute 6 times 7.")
        assert first.stage == "CLOSED_CANCELLED" if failed else first.refused
        worker.sys1_client.p_poisoned = 0.02
        worker.sys1_client.problem_class = "STANDARD_EXECUTION"
        _assert_direct_evidence(session.send("Explain one idea."))


def test_unfinished_review_reopen_preserves_turn_source_and_controller(tmp_path):
    folder = tmp_path / "s"
    with api.Session.open(DirectWorker(), folder, repo_root=ROOT, mode="protocol", no_review=False) as session:
        first = session.send("Explain one idea.")
        assert first.stage == "PROMPT_REVIEW"
        workspace = session.status()["workspace_path"]
        prompt = session.host.engine.controller.state.current_prompt.body
    with api.Session.open(DirectWorker(), folder, repo_root=ROOT, no_review=False) as session:
        assert session.status()["workspace_path"] == workspace
        assert session.host.engine.workspace.turn_id == "turn_001"
        assert session.host.engine.workspace.turn_source() == "Explain one idea."
        assert session.host.engine.controller.state.current_prompt.body == prompt
        assert session.confirm().stage == "PLAN_REVIEW"
        assert session.confirm().stage == "CLOSED_UNVERIFIED"


def test_failure_disclosure_stays_with_its_published_protocol_turn(tmp_path, monkeypatch):
    with api.Session.open(MixedWorker(), tmp_path / "s", repo_root=ROOT, mode="protocol") as session:
        monkeypatch.setattr(session.host.engine.sandbox, "run_code",
                            lambda *a, **k: SandboxResult("", "failed", 1, 1, steps_used=1))
        first = session.send("Deliver an example program.")
        assert first.provenance["verification"]["run_failures_not_fed_back"]
        monkeypatch.setattr(session.host.engine.sandbox, "run_code", _recorded_sandbox)
        second = session.send("Deliver another example program.")
        assert second.stage == "CLOSED_UNVERIFIED"
        assert "run_failures_not_fed_back" not in second.provenance["verification"]
