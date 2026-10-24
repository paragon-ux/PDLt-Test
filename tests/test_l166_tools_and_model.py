"""L166: in-call tools are on by default except on the unconfirmed route (protocol mode, no review), in the REPL, the
API and the catalogue runner; a flag or $PDLT_AGENT_TOOLS wins. L167: openai/gpt-oss-120b is the default model. L164's
13-06 rule: where clarification is the ground truth, an unverified answer awaits a human check. Offline."""
from __future__ import annotations

import pytest

import graders
import run_catalogue
from pdl_taskmaster import api
from pdl_taskmaster.host import repl
from pdl_taskmaster.providers.api_worker import ApiWorker
from pdl_taskmaster.runtime.run_settings import default_agent_tools

from test_adr0031_defaults import _api_worker
from test_api import ROOT


@pytest.mark.parametrize("mode, no_review, expected", [
    ("protocol", True, False), ("protocol", False, True), ("saver", True, True), ("direct", True, True)])
def test_the_rule(mode, no_review, expected):
    assert default_agent_tools(mode, no_review) is expected


@pytest.mark.parametrize("argv, env, expected", [
    ([], None, True),                                   # saver
    (["--mode", "protocol"], None, False),              # the unconfirmed route
    (["--review"], None, True),                         # the confirmed route
    (["--mode", "protocol", "--agent-tools"], None, True),
    (["--mode", "protocol"], "1", True),                # the environment wins over the route default
    ([], "0", False),
])
def test_the_repl_applies_it(monkeypatch, argv, env, expected):
    if env is None:
        monkeypatch.delenv("PDLT_AGENT_TOOLS", raising=False)
    else:
        monkeypatch.setenv("PDLT_AGENT_TOOLS", env)
    assert repl._run_settings(repl._build_parser().parse_args(argv), _api_worker()).agent_tools is expected


@pytest.mark.parametrize("worker_tools, mode, expected", [(None, "protocol", False), (None, None, True),
                                                          (True, "protocol", True)])
def test_the_api_applies_it(tmp_path, monkeypatch, worker_tools, mode, expected):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    worker = ApiWorker(repo_root=ROOT, agent_tools=worker_tools)
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode=mode) as session:
        assert session.host.engine.agent_tools is expected


def test_the_catalogue_runner_applies_it():
    assert [run_catalogue.default_agent_tools(r) for r in ("unconfirmed", "confirmed", "saver", "direct", "control")] \
        == [False, True, True, True, False]


def test_gpt_oss_120b_is_the_default_model():
    assert repl._build_parser().parse_args([]).model == "openai/gpt-oss-120b"
    assert ApiWorker(repo_root=ROOT).model == "openai/gpt-oss-120b"


@pytest.mark.parametrize("verdict, grade, outcome", [
    ("CLOSED_UNVERIFIED", graders.PASS, "PENDING"), ("CLOSED_UNVERIFIED", graders.NA, "PENDING"),
    ("CLOSED_UNVERIFIED", graders.FAIL, "FAIL"), ("WAITING_INPUT", graders.PASS, "PASS")])
def test_an_unverified_answer_to_a_clarification_prompt_awaits_a_human_check(verdict, grade, outcome):
    r = {"expected_stage": "WAITING_INPUT", "verdict": verdict, "ground_truth_grade": {"grade": grade}}
    assert run_catalogue.outcome_class(r) == outcome
