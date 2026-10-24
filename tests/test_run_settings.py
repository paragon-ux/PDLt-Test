"""L124 D7: typed run settings, System 1 as its own provider, and the direct reply inside the engine. Offline."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from pdl_taskmaster import api
from pdl_taskmaster.extensions.conformance import ScriptedSys1, ScriptedWorker
from pdl_taskmaster.host import repl
from pdl_taskmaster.providers.base import WorkerResult
from pdl_taskmaster.runtime.run_settings import RunSettings
from pdl_taskmaster.runtime.session_engine import SessionEngine

from extension_samples import POSITIVE_SAMPLE

ROOT = Path(__file__).resolve().parents[1]


# Typed settings.

def test_invalid_settings_are_refused_naming_each_field():
    with pytest.raises(ValueError) as caught:
        RunSettings(max_repairs=-1, representation="html", sandbox_mode=3, draft_execute="yes")
    for name in ("max_repairs", "representation", "sandbox_mode", "draft_execute"):
        assert f"{name}:" in str(caught.value)


def test_settings_read_from_a_worker_match_what_the_host_used_to_copy():
    carrying = SimpleNamespace(max_repairs=0, draft_execute=1, agent_tools=True, representation=None, tier_d1=None)
    assert RunSettings.from_worker(carrying) == RunSettings(max_repairs=0, draft_execute=True, agent_tools=True)
    # A worker that carries no settings runs as its recordings were made: protocol mode, no in-call tools (ADR-0031).
    assert RunSettings.from_worker(object(), no_review=True) == RunSettings(no_review=True, agent_tools=False,
                                                                            mode="protocol")


def test_a_session_applies_its_settings_and_refuses_them_twice(tmp_path):
    settings = RunSettings(max_repairs=0, draft_execute=True, tier_d1=True, no_review=True)
    with api.Session.open(ScriptedWorker({"body": "x"}), tmp_path / "s", repo_root=ROOT, settings=settings) as session:
        engine = session.host.engine
        assert (engine.max_repairs, engine.draft_execute, engine.tier_d1, engine.no_review) == (0, True, True, True)
    with pytest.raises(ValueError, match="pass no_review, sandbox_mode, task_type and mode in settings"):
        api.Session.open(ScriptedWorker({"body": "x"}), tmp_path / "t", settings=settings, no_review=False)


def test_the_repl_builds_typed_settings_from_its_flags(monkeypatch):
    from pdl_taskmaster.providers.api_worker import ApiWorker

    args = repl._build_parser().parse_args(["--task-type", "STANDARD_EXECUTION", "--max-repairs", "0",
                                            "--draft-execute", "--review"])
    api_worker = ApiWorker(model="lab/model", repo_root=ROOT)
    settings = repl._run_settings(args, api_worker)
    assert (settings.task_type, settings.max_repairs, settings.draft_execute, settings.no_review) == (
        "STANDARD_EXECUTION", 0, True, False)
    # A recorded replay keeps the defaults its recordings were made with.
    assert repl._run_settings(args, ScriptedWorker({})) == RunSettings(task_type="STANDARD_EXECUTION", agent_tools=False,
                                                                       mode="protocol", no_review=False)


# System 1 as its own provider.

def test_a_session_takes_system_1_apart_from_the_worker(tmp_path):
    worker = ScriptedWorker(POSITIVE_SAMPLE, sys1=None)
    sys1 = ScriptedSys1({"problem_class": ("VERIFIED_EXECUTION", 0.97)})
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, sys1=sys1, mode="protocol") as session:
        result = session.run("Find the largest product.", confirm=True)
    assert result.provenance["verification"]["problem_class"] == "VERIFIED_EXECUTION"
    assert worker.sys1_client is sys1  # the worker uses the same System 1
    assert [r["questions"] and next(iter(r["questions"])) for r in sys1.requests][:2] == ["route", "problem_class"]


# The direct reply is the engine's.

class Bypassing(ScriptedSys1):
    def call(self, request):
        name = next(iter(request.questions))
        if name != "route":
            return super().call(request)
        self.requests.append(request.to_dict())
        return {"answers": {"route": {"choice": "BYPASS", "confidence": 0.97,
                                      "probabilities": {"BYPASS": 0.97, "APPLY_PROTOCOL": 0.03}}}}, 1.0


class Plain(ScriptedWorker):
    def call(self, request):
        if request.operation == "BYPASS_ORDINARY":
            self.requests.append((request.operation, request.prompt))
            self.environment = request.environment
            return WorkerResult(json.dumps({"message": "PDLt runs tasks under a protocol."}))
        return super().call(request)


def test_a_direct_reply_comes_back_from_the_session(tmp_path):
    worker = Plain({"body": "x"}, Bypassing())
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, no_review=True, mode="protocol") as session:
        result = session.send("What is PDLt?")
    assert (result.text, result.stage, result.exit_status) == ("PDLt runs tasks under a protocol.", None, 0)
    assert worker.requests == [("BYPASS_ORDINARY", "What is PDLt?")]
    assert "Programs run only when a task is executed" in worker.environment


def test_the_engine_replies_to_the_users_own_words(tmp_path):
    seen = []
    engine = SessionEngine(ROOT, lambda request: "", workspace_root=tmp_path, sys1_client=Bypassing(), no_review=True)
    engine.plain_reply = lambda text, environment: seen.append(text) or "a reply"
    response = engine.handle_user_message("routed form of the message", user_text="the user's own words")
    assert (response.text, response.bypass, seen) == ("a reply", True, ["the user's own words"])
