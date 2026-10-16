"""L120: the library layer (pdl_taskmaster.api) that the REPL, headless runs and the MCP server go through.

Offline; the worker is scripted and System 1 is a fake.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import run_catalogue
from pdl_taskmaster import api
from pdl_taskmaster.api import outcome, providers
from pdl_taskmaster.host import mcp_server, repl
from pdl_taskmaster.providers.base import WorkerResult
from pdl_taskmaster.verification.output_verifier import OutputVerifier

from test_execution_phase import PLAN, PROMPT, _ir
from test_l116_closure import POSITIVE, VERIFIED
from test_unconfirmed_route import ClassifyingSys1, _bootstrap_reply, _unconfirmed_result_reply

ROOT = Path(__file__).resolve().parents[1]
REQUEST = "Solve the stated task."


class ScriptedWorker:
    """Answers each operation of the confirmed and unconfirmed routes; EXECUTE returns ``body``."""

    def __init__(self, body: str = "The answer is 42.", problem_class: str = "STANDARD_EXECUTION"):
        self.body = body
        self.sys1_client = ClassifyingSys1(problem_class)
        self.operations: list[str] = []

    def call(self, request) -> WorkerResult:
        self.operations.append(request.operation)
        replies = {
            "BOOTSTRAP_ANALYSIS": _bootstrap_reply("The user states a task to solve.", []),
            "DRAFT_PROMPT": json.dumps({"kind": "PROMPT", "prompt_body": PROMPT, "approach_handoff": "NONE"}),
            "DRAFT_PLAN": json.dumps({"neutral_plan_body": PLAN}),
            "EXECUTE": json.dumps({"kind": "RESULT", "body": self.body, "result_ir": _ir()}),
            "EXECUTE_UNCONFIRMED": _unconfirmed_result_reply(),
        }
        return WorkerResult(replies[request.operation])


# Exit status: one mapping.

@pytest.mark.parametrize("stage, refused, harness_error, code", [
    ("CLOSED_SUCCESS", False, False, 0),
    (None, False, False, 0),  # a direct reply
    (None, True, False, 0),  # a published boundary refusal
    ("CLOSED_CANCELLED", False, False, 1),
    ("PROMPT_REVIEW", False, False, 2),
    ("PLAN_REVIEW", False, False, 2),
    ("WAITING_INPUT", False, False, 3),
    ("CLOSED_SUCCESS", False, True, 4),
    ("CLOSED_UNVERIFIED", False, False, 5),
])
def test_exit_status_follows_adr_0019(stage, refused, harness_error, code):
    assert outcome.exit_status(stage, refused=refused, harness_error=harness_error) == code


def test_the_repl_and_the_catalogue_use_the_one_mapping():
    for name in ("EXIT_SUCCESS", "EXIT_CANCELLED", "EXIT_UNCONFIRMED", "EXIT_WAITING_INPUT", "EXIT_HARNESS_ERROR",
                 "EXIT_UNVERIFIED"):
        assert getattr(run_catalogue, name) == getattr(outcome, name)
    assert (repl.EXIT_HARNESS_ERROR, repl.EXIT_UNVERIFIED) == (outcome.EXIT_HARNESS_ERROR, outcome.EXIT_UNVERIFIED)


# Providers: a registry, not an if-chain.

@pytest.fixture
def registry(monkeypatch):
    monkeypatch.setattr(providers, "_FACTORIES", dict(providers._FACTORIES))


def test_the_built_in_providers_are_registered():
    assert {"api", "recorded"} <= set(api.provider_names())


def test_the_api_provider_passes_its_settings_to_the_worker():
    from pdl_taskmaster.providers.api_worker import ApiWorker

    worker = api.create_worker("api", model="lab/model", repo_root=ROOT, max_output_tokens=4096)
    assert isinstance(worker, ApiWorker) and worker.model == "lab/model"


def test_the_recorded_provider_needs_an_eval_root_except_for_a_vendored_fixture(monkeypatch):
    from pdl_taskmaster.providers import fixtures

    seen = []
    monkeypatch.setattr(fixtures, "build_recorded_fixture_from_vendored",
                        lambda repo, path, case_ids=None: seen.append((repo, path.name, case_ids)) or "worker")
    assert api.create_worker("recorded", repo_root=ROOT, evidence="x/recorded-cases.json", case_ids=["a"]) == "worker"
    assert seen == [(ROOT, "recorded-cases.json", ["a"])]
    with pytest.raises(ValueError, match="eval_root"):
        api.create_worker("recorded", repo_root=ROOT, evidence="evidence.jsonl")


def test_a_provider_can_be_registered_and_an_unknown_one_is_named(registry):
    api.register_provider("scripted", lambda **settings: ScriptedWorker(**settings))
    assert isinstance(api.create_worker("scripted", body="x"), ScriptedWorker)
    with pytest.raises(ValueError, match="already registered"):
        api.register_provider("scripted", ScriptedWorker)
    api.register_provider("scripted", lambda **settings: "replaced", replace=True)
    assert api.create_worker("scripted") == "replaced"
    with pytest.raises(ValueError, match=r"unknown provider 'nope'; known: .*api.*recorded"):
        api.create_worker("nope")


# Session: the confirmed route, the unconfirmed route, resumption.

def test_a_session_walks_the_confirmed_route_to_a_result_with_its_provenance(tmp_path):
    with api.Session.open(ScriptedWorker(), tmp_path / "s-1", repo_root=ROOT) as session:
        prompt = session.send(REQUEST)
        assert (prompt.stage, prompt.review, prompt.exit_status, prompt.closed) == ("PROMPT_REVIEW", "prompt", 2, False)
        assert PROMPT.splitlines()[0] in prompt.text and prompt.provenance is None
        plan = session.confirm()
        assert (plan.stage, plan.review, plan.exit_status) == ("PLAN_REVIEW", "plan", 2)
        result = session.confirm()
    assert (result.stage, result.exit_status, result.closed, result.review) == ("CLOSED_SUCCESS", 0, True, None)
    assert "The answer is 42." in result.text
    assert result.provenance["verification"]["level"] == "contract_checked"
    pointer = json.loads((tmp_path / "s-1" / "session.json").read_text(encoding="utf-8"))
    assert pointer["workspace_relpath"] == Path(result.workspace_path).relative_to(tmp_path / "s-1").as_posix()


def test_run_with_confirm_accepts_each_review_as_a_standing_confirmation(tmp_path):
    worker = ScriptedWorker(POSITIVE, VERIFIED)
    with api.Session.open(worker, tmp_path / "s-1", repo_root=ROOT) as session:
        result = session.run(REQUEST, confirm=True)
        events = [e["kind"] for e in session.host.engine.workspace.read_events()]
    assert result.stage == "CLOSED_SUCCESS" and result.provenance["verification"]["level"] == "host_verified"
    assert events.count("STANDING_CONFIRMATION") == 2
    assert worker.operations == ["BOOTSTRAP_ANALYSIS", "DRAFT_PROMPT", "DRAFT_PLAN", "EXECUTE"]


def test_run_without_confirm_stops_at_the_review(tmp_path):
    with api.Session.open(ScriptedWorker(), tmp_path / "s-1", repo_root=ROOT) as session:
        result = session.run(REQUEST)
    assert (result.stage, result.exit_status) == ("PROMPT_REVIEW", outcome.EXIT_UNCONFIRMED)


def test_no_review_takes_the_unconfirmed_route_in_one_message(tmp_path):
    worker = ScriptedWorker()
    with api.Session.open(worker, tmp_path / "s-1", repo_root=ROOT, no_review=True) as session:
        result = session.send(REQUEST)
    assert (result.stage, result.exit_status, result.closed) == ("CLOSED_SUCCESS", 0, True)
    assert worker.operations == ["BOOTSTRAP_ANALYSIS", "EXECUTE_UNCONFIRMED"]


def test_reopening_a_session_resumes_its_workspace(tmp_path):
    with api.Session.open(ScriptedWorker(), tmp_path / "s-1", repo_root=ROOT) as session:
        first = session.send(REQUEST)
    with api.Session.open(ScriptedWorker(), tmp_path / "s-1", repo_root=ROOT) as resumed:
        assert resumed.status()["workspace_path"] == first.workspace_path
        assert resumed.status()["controller_state"]["stage"] == "PROMPT_REVIEW"
    with api.Session.open(ScriptedWorker(), tmp_path / "s-1", repo_root=ROOT, restore=False) as fresh:
        assert fresh.status()["workspace_path"] is None


def test_a_review_command_with_no_open_review_is_not_a_request(tmp_path):
    worker = ScriptedWorker()
    with api.Session.open(worker, tmp_path / "s-1", repo_root=ROOT) as session:
        result = session.confirm()
    assert result.stage is None and result.exit_status == 0 and worker.operations == []


# Verification: the registry is injectable.

def test_a_caller_supplied_verifier_is_the_one_the_result_is_checked_against(tmp_path):
    class Recording(OutputVerifier):
        def __init__(self):
            super().__init__()
            self.checked = 0

        def check(self, *args, **kwargs):
            self.checked += 1
            return super().check(*args, **kwargs)

    verifier = Recording()
    with api.Session.open(ScriptedWorker(POSITIVE, VERIFIED), tmp_path / "s-1", repo_root=ROOT,
                          output_verifier=verifier) as session:
        assert session.host.engine.output_verifier is verifier
        result = session.run(REQUEST, confirm=True)
    assert result.stage == "CLOSED_SUCCESS" and verifier.checked >= 1


# Closed sessions: one reader, the MCP resources built on it.

def test_closed_turns_and_the_mcp_resources_agree(tmp_path):
    sessions = tmp_path / "sessions"
    with api.Session.open(ScriptedWorker(POSITIVE, VERIFIED), sessions / "s-1", repo_root=ROOT) as session:
        result = session.run(REQUEST, confirm=True)
        session.send("Solve another stated task.")  # left open at its review: not served
    turns = api.closed_turns(sessions)
    assert [(t.session, t.status) for t in turns] == [("s-1", "CLOSED_SUCCESS")]
    turn = turns[0]
    assert turn.provenance() == result.provenance
    assert set(turn.artifacts()) == {"response", "program-output"}
    prefix = f"pdlt://sessions/{turn.session}/{turn.workspace}/{turn.turn}/"
    served = mcp_server.ClosedSessions(sessions).resources()
    assert set(served) == {prefix + "provenance", prefix + "response", prefix + "program-output"}
    assert json.loads(served[prefix + "provenance"][0]()) == result.provenance


def test_an_artifact_outside_the_sessions_folder_is_not_served(tmp_path):
    sessions = tmp_path / "sessions"
    turn = sessions / "s-1" / "workspaces" / "w" / "turns" / "turn_001"
    output = turn / "stages" / "50_execution" / "output"
    output.mkdir(parents=True)
    (turn / "turn.json").write_text(json.dumps({"status": "CLOSED_SUCCESS"}), encoding="utf-8")
    outside = tmp_path / "secret.md"
    outside.write_text("outside", encoding="utf-8")
    try:
        (output / "current.md").symlink_to(outside)
    except OSError:
        pytest.skip("symbolic links are not available here")
    (turn_only,) = api.closed_turns(sessions)
    assert turn_only.artifacts() == {}


# Sandbox: one factory.

def test_the_sandbox_factory_refuses_the_audit_only_opt_out_when_confinement_is_required():
    with pytest.raises(api.SandboxNotConfined, match="audit-only"):
        api.create_sandbox("audit-only", label="api-test", require_confined=True)
    assert api.create_sandbox("audit-only", label="api-test").confined is False
