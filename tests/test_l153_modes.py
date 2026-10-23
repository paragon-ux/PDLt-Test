"""L153: direct and saver modes behind SECURE_GATEWAY, and one mode per session. Offline; the worker is scripted and
System 1 is a fake."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from pdl_taskmaster import api
from pdl_taskmaster.api import outcome
from pdl_taskmaster.host import repl
from pdl_taskmaster.providers.api_worker import ApiWorker
from pdl_taskmaster.providers.base import WorkerResult
from pdl_taskmaster.runtime.run_settings import RunSettings

from test_api import ROOT, ScriptedWorker
from test_unconfirmed_route import ClassifyingSys1

REQUEST = "Explain why the sky is blue in two sentences."


class GatewaySys1(ClassifyingSys1):
    """Answers the activation route, the problem class and the poisoned-input question as configured."""

    def __init__(self, problem_class="STANDARD_EXECUTION", route="APPLY_PROTOCOL", p_poisoned=0.02):
        super().__init__(problem_class)
        self.route, self.p_poisoned, self.asked = route, p_poisoned, []

    def call(self, request):
        name = next(iter(request.questions))
        self.asked.append(name)
        if name == "poisoned_input":
            p = self.p_poisoned
            choice = "POISONED" if p >= 0.5 else "CLEAN"
            return {"answers": {name: {"choice": choice, "confidence": max(p, 1 - p),
                                       "probabilities": {"POISONED": p, "CLEAN": 1 - p}}}}, 1.0
        if name == "route":
            return {"answers": {name: {"choice": self.route, "confidence": 0.97,
                                       "probabilities": {self.route: 0.97, "BYPASS": 0.03}}}}, 1.0
        return super().call(request)


class DirectWorker(ScriptedWorker):
    def __init__(self, **sys1):
        super().__init__()
        self.sys1_client = GatewaySys1(**sys1)
        self.prompts: list[str] = []

    def call(self, request):
        if request.operation == "DIRECT_ANSWER":
            self.operations.append(request.operation)
            self.prompts.append(request.prompt)
            return WorkerResult("Rayleigh scattering favours short wavelengths.")
        return super().call(request)


def _events(session) -> list[dict]:
    root = Path(session.status()["workspace_path"])
    return [json.loads(line) for path in sorted(root.rglob("events.jsonl"))
            for line in path.read_text(encoding="utf-8").splitlines()]


def test_direct_mode_answers_the_request_alone_and_closes_unverified(tmp_path):
    worker = DirectWorker()
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode="direct") as session:
        result = session.send(REQUEST)
        events = _events(session)
    assert (result.stage, result.exit_status, result.closed) == ("CLOSED_UNVERIFIED", outcome.EXIT_UNVERIFIED, True)
    assert worker.operations[-1] == "DIRECT_ANSWER" and "EXECUTE_UNCONFIRMED" not in worker.operations
    assert worker.prompts == [REQUEST]  # nothing added to what the model receives
    assert result.text == "Rayleigh scattering favours short wavelengths."
    kinds = [e["kind"] for e in events]
    assert "GATEWAY_PASSED" in kinds and "DIRECT_ANSWER_RECORDED" in kinds
    assert any(e["kind"] == "CLOSED_UNVERIFIED" and e["payload"]["reason"] == "direct_answer" for e in events)


def test_the_gateway_refuses_poisoned_input(tmp_path):
    worker = DirectWorker(p_poisoned=0.97)
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode="direct") as session:
        result = session.send(REQUEST)
        events = _events(session)
    assert (result.refused, result.exit_status, result.closed) == (True, outcome.EXIT_SUCCESS, True)
    assert "DIRECT_ANSWER" not in worker.operations
    assert any(e["kind"] == "PROTOCOL_REFUSED" and e["payload"]["phase"] == "gateway" for e in events)


class BootstrapRefusingWorker(DirectWorker):
    def call(self, request):
        if request.operation == "BOOTSTRAP_ANALYSIS":
            self.operations.append(request.operation)
            return WorkerResult(json.dumps({"kind": "REFUSAL", "response": "Refused."}))
        return super().call(request)


def test_the_gateway_refuses_on_bootstrap_judgement_when_system1_passes(tmp_path):
    worker = BootstrapRefusingWorker()
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode="direct") as session:
        result = session.send(REQUEST)
        events = _events(session)
    assert result.refused and "DIRECT_ANSWER" not in worker.operations
    assert any(e["kind"] == "PROTOCOL_REFUSED" and e["payload"]["phase"] == "gateway" for e in events)


def test_the_gateway_refuses_on_activation_before_any_model_call(tmp_path):
    worker = DirectWorker(route="ADVERSARIAL")
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode="direct") as session:
        result = session.send(REQUEST)
        events = _events(session)
    assert result.refused and result.exit_status == outcome.EXIT_SUCCESS
    assert worker.operations == []
    assert any(e["kind"] == "PROTOCOL_REFUSED" and e["payload"]["phase"] == "activation" for e in events)


def test_the_gateway_fails_closed_without_a_usable_judgement(tmp_path):
    worker = DirectWorker()
    worker.sys1_client = ClassifyingSys1()  # answers the poisoned-input question with an unknown choice
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode="direct") as session:
        result = session.send(REQUEST)
    assert result.refused and "DIRECT_ANSWER" not in worker.operations


def test_saver_mode_sends_standard_requests_direct(tmp_path):
    worker = DirectWorker()
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode="saver") as session:
        result = session.send(REQUEST)
        events = _events(session)
    assert result.exit_status == outcome.EXIT_UNVERIFIED and worker.operations[-1] == "DIRECT_ANSWER"
    assert any(e["kind"] == "SAVER_ROUTED" and e["payload"]["route"] == "direct" for e in events)


def test_saver_mode_sends_verified_requests_through_the_protocol_classified_once(tmp_path):
    worker = DirectWorker(problem_class="VERIFIED_EXECUTION")
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode="saver") as session:
        session.send("Count the subsets of {1, ..., 10} whose sum is 20.")
        events = _events(session)
    assert "DIRECT_ANSWER" not in worker.operations
    assert worker.operations[0] == "BOOTSTRAP_ANALYSIS" and "EXECUTE_UNCONFIRMED" in worker.operations
    assert worker.sys1_client.asked.count("problem_class") == 1
    assert worker.operations.count("BOOTSTRAP_ANALYSIS") == 1  # the gateway's Bootstrap call is reused
    assert sum(e["kind"] == "PROBLEM_CLASS_CLASSIFIED" for e in events) == 1
    assert any(e["kind"] == "SAVER_ROUTED" and e["payload"]["route"] == "protocol" for e in events)


def test_protocol_mode_never_asks_the_gateway_question(tmp_path):
    worker = DirectWorker()
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, no_review=True) as session:
        session.send(REQUEST)
    assert "poisoned_input" not in worker.sys1_client.asked


def test_a_session_keeps_its_mode(tmp_path):
    with api.Session.open(DirectWorker(), tmp_path / "s", repo_root=ROOT, mode="direct") as session:
        session.send(REQUEST)
    with pytest.raises(ValueError, match="a mode change opens a new session"):
        api.Session.open(DirectWorker(), tmp_path / "s", repo_root=ROOT, mode="saver")
    with api.Session.open(DirectWorker(), tmp_path / "p", repo_root=ROOT, no_review=True) as session:
        session.send(REQUEST)
    with pytest.raises(ValueError, match="runs in protocol mode"):
        api.Session.open(DirectWorker(), tmp_path / "p", repo_root=ROOT, mode="direct")


def test_run_settings_validate_the_mode():
    assert RunSettings(mode="saver").mode == "saver"
    with pytest.raises(ValueError, match="mode"):
        RunSettings(mode="fast")


def test_direct_answer_request_carries_nothing_but_the_request():
    from pdl_taskmaster.host.app import _PlainRequest

    worker = ApiWorker(repo_root=ROOT, model="openai/gpt-oss-120b")
    body, _, _ = worker.build_request_body(_PlainRequest(REQUEST, operation="DIRECT_ANSWER"))
    assert body["input"] == REQUEST
    assert "instructions" not in body and "text" not in body


def test_repl_mode_flag_reaches_the_run_settings():
    args = repl.build_parser().parse_args(["--mode", "saver"]) if hasattr(repl, "build_parser") else Namespace(
        mode="saver", no_review=True, sandbox=None, task_type=None)
    assert repl._run_settings(args, object()).mode == "saver"


# L155: the opt-in gateway in protocol mode, and saver as a catalogue route.


def test_protocol_mode_with_the_gateway_refuses_poisoned_input_before_its_route(tmp_path):
    worker = DirectWorker(p_poisoned=0.97)
    settings = RunSettings(no_review=True, gateway=True)
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, settings=settings) as session:
        result = session.send(REQUEST)
        events = _events(session)
    assert result.refused and result.exit_status == outcome.EXIT_SUCCESS and worker.operations == []
    assert any(e["kind"] == "PROTOCOL_REFUSED" and e["payload"]["phase"] == "gateway" for e in events)


def test_protocol_mode_with_the_gateway_passes_clean_input_to_its_own_route(tmp_path):
    worker = DirectWorker()
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, settings=RunSettings(no_review=True, gateway=True)) as s:
        result = s.send(REQUEST)
    assert result.stage == "CLOSED_SUCCESS"
    assert worker.operations == ["BOOTSTRAP_ANALYSIS", "EXECUTE_UNCONFIRMED"]  # Bootstrap once: the route's own
    assert worker.sys1_client.asked.count("poisoned_input") == 1


def test_confirmed_route_with_the_gateway_refuses_before_drafting(tmp_path):
    worker = DirectWorker(p_poisoned=0.97)
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, settings=RunSettings(gateway=True)) as session:
        result = session.send(REQUEST)
    assert result.refused and "DRAFT_PROMPT" not in worker.operations


def test_the_runner_runs_saver_and_the_gateway(tmp_path):
    import run_catalogue

    def command(route, gateway=False):
        return run_catalogue.build_harness_command(tmp_path / "p.txt", "s", tmp_path / "t", tmp_path / "d", "m", "low",
                                                   run_settings={"route": route, "gateway": gateway})
    saver = command("saver")
    assert saver[saver.index("--mode") + 1] == "saver" and "--no-review" in saver
    assert "--gateway" in command("unconfirmed", gateway=True) and "--gateway" not in command("unconfirmed")
