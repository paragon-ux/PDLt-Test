"""ADR-0031: the default configuration is saver mode with in-call tools at low reasoning, and saver sends Cerebras
first (option (b)); a worker that carries no settings runs as its recordings were made. Offline."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from pdl_taskmaster import api
from pdl_taskmaster.api.session import stored_session_mode
from pdl_taskmaster.host import repl
from pdl_taskmaster.providers.api_worker import (DEFAULT_PROVIDER_PINNING, SAVER_PROVIDER_PINNING, ApiWorker,
                                                 mode_pinning)
from pdl_taskmaster.runtime.run_settings import RunSettings, default_mode

from test_api import ROOT, ScriptedWorker

MODEL = "openai/gpt-oss-120b"


def _api_worker(**settings) -> ApiWorker:
    return ApiWorker(model=MODEL, repo_root=ROOT, **settings)


def test_the_repl_defaults_to_saver_with_tools_on(monkeypatch):
    monkeypatch.delenv("PDLT_AGENT_TOOLS", raising=False)
    settings = repl._run_settings(repl._build_parser().parse_args([]), _api_worker())
    assert (settings.mode, settings.agent_tools) == ("saver", True)


@pytest.mark.parametrize("argv, env, expected", [
    (["--no-agent-tools"], None, False),
    ([], "0", False),
    (["--agent-tools"], "0", True),  # the flag wins over the environment
])
def test_tools_turn_off_by_flag_or_environment(monkeypatch, argv, env, expected):
    if env is None:
        monkeypatch.delenv("PDLT_AGENT_TOOLS", raising=False)
    else:
        monkeypatch.setenv("PDLT_AGENT_TOOLS", env)
    assert repl._run_settings(repl._build_parser().parse_args(argv), _api_worker()).agent_tools is expected


def test_an_explicit_mode_wins():
    args = repl._build_parser().parse_args(["--mode", "protocol"])
    assert repl._run_settings(args, _api_worker()).mode == "protocol"


def test_the_api_worker_runs_saver_with_tools_and_a_worker_with_no_settings_runs_as_recorded():
    assert default_mode(_api_worker()) == "saver" and _api_worker().agent_tools is None  # the session's default
    assert (RunSettings.from_worker(_api_worker()).mode, RunSettings.from_worker(_api_worker()).agent_tools) == (
        "saver", True)
    recorded = RunSettings.from_worker(ScriptedWorker())
    assert (recorded.mode, recorded.agent_tools) == ("protocol", False)


def test_saver_with_tools_sends_cerebras_first_and_the_other_modes_keep_the_default_order():
    assert SAVER_PROVIDER_PINNING["order"][0] == "Cerebras"
    assert mode_pinning("saver", True) == SAVER_PROVIDER_PINNING
    # Without tools saver's execution is sent in JSON mode, where Cerebras drops the free-form witness.
    assert mode_pinning("saver", False) is None
    assert mode_pinning("protocol", True) is None and mode_pinning("direct", True) is None
    worker = _api_worker()
    worker.mode_pinning = mode_pinning("saver", True)
    assert worker.pinning_for(MODEL) == SAVER_PROVIDER_PINNING
    assert worker.pinning_for("lab/other-model") == {}  # only families with recorded settings get an order
    worker.mode_pinning = None
    assert worker.pinning_for(MODEL) == DEFAULT_PROVIDER_PINNING


def test_a_configured_order_wins_over_the_mode_order():
    worker = _api_worker(provider_pinning={"order": ["Baseten"], "allow_fallbacks": False})
    worker.mode_pinning = mode_pinning("saver", True)
    assert worker.pinning_for(MODEL) == {"order": ["Baseten"], "allow_fallbacks": False}


@pytest.mark.parametrize("mode, expected", [(None, SAVER_PROVIDER_PINNING), ("protocol", None)])
def test_a_session_sets_its_mode_order_on_the_worker(tmp_path, monkeypatch, mode, expected):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    worker = _api_worker()
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode=mode) as session:
        assert session.host.engine.mode == (mode or "saver")
        assert worker.mode_pinning == expected


def test_a_resumed_session_keeps_its_own_mode(tmp_path):
    assert stored_session_mode(tmp_path, restoring=False) is None
    assert stored_session_mode(tmp_path, restoring=True) == "protocol"  # history from before the mode file
    (tmp_path / "mode.json").write_text(json.dumps({"mode": "direct"}) + "\n", encoding="utf-8")
    assert stored_session_mode(tmp_path, restoring=True) == "direct"


def test_the_runner_names_the_mode_and_the_tools_for_every_harness_route(tmp_path):
    import run_catalogue

    def command(route, **settings):
        return run_catalogue.build_harness_command(tmp_path / "p.txt", "s", tmp_path / "t", tmp_path / "d", "m", "low",
                                                   run_settings={"route": route, **settings})
    for route, mode in (("unconfirmed", "protocol"), ("confirmed", "protocol"), ("saver", "saver"),
                        ("direct", "direct")):
        args = command(route)
        assert args[args.index("--mode") + 1] == mode and "--no-agent-tools" in args
    assert "--agent-tools" in command("saver", agent_tools=True)
    control = command("control")
    assert "--mode" not in control and "--agent-tools" not in control and "--no-agent-tools" not in control


def test_experiment_arms_run_as_before_unless_they_name_a_mode_or_tools():
    sys.path.insert(0, str(ROOT / "experiments"))
    import runner

    spec = runner.ArmSpec(name="P", kind="protocol", worktree=ROOT)
    assert runner._default_args(spec, ()) == ["--mode", "protocol", "--agent-tools"]  # reviewed: the confirmed route
    assert runner._default_args(spec, ("--no-review",)) == ["--mode", "protocol", "--no-agent-tools"]  # L166
    assert runner._default_args(spec, ("--mode", "saver", "--agent-tools")) == []
