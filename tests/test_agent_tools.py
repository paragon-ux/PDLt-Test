"""ADR-0029: in-call agent tools on EXECUTE_UNCONFIRMED. Off by default; when on, the engine attaches a tool host
(its own sandbox, budget and checks) to the request and the API worker runs the loop. The engine verifies the
accepted reply as any reply. No model call: the worker is scripted."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdl_taskmaster.controller.mechanical_controller import Stage
from pdl_taskmaster.providers.api_worker import ApiWorker
from pdl_taskmaster.runtime import agent_tools
from pdl_taskmaster.runtime.agent_tools import MAX_SUBMISSIONS, MAX_TOOL_CALLS, SUBMIT, TOOLS, ToolHost, run_loop
from pdl_taskmaster.runtime.operation_bridge import OperationBridge
from pdl_taskmaster.runtime.session_engine import (SessionEngine, _parse_sandbox_witness, _python_blocks,
                                                   _witness_written_in_program)
from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS, ExecutionSandbox

from test_computation_recipe import Sys1, _bootstrap

ROOT = Path(__file__).resolve().parents[1]
BUDGET = EXECUTION_BUDGETS["STANDARD"]
GOOD = "import json\nprint('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'x': 6 * 7}}))"
SLOW = "while True:\n    pass"
IR = {"files": [], "reconciliation": [], "open_defects": []}


def outcome(body: str) -> dict:
    return {"kind": "RESULT", "interpretation": "DETERMINE the result", "approach": "COMPUTE it", "body": body,
            "result_ir": IR}


def _engine(tmp_path: Path, execute, *, agent_tools_on: bool, problem_class: str = "VERIFIED_EXECUTION",
            exclude: str | None = None):
    requests: list = []

    def model_call(req):
        requests.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return _bootstrap()
        if req.operation == "EXECUTE_UNCONFIRMED":
            return execute(req)
        raise AssertionError(req.operation)

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=Sys1(problem_class), no_review=True)
    engine.agent_tools = agent_tools_on
    engine.agent_tools_exclude = agent_tools.parse_exclusions(exclude)
    response = engine.handle_user_message("Count the subsets of 1..10 that sum to 20.")
    return engine, response, requests, list(engine.workspace.read_events())


def _host(validate=None, programs=(), correction=""):
    return ToolHost(ExecutionSandbox(), BUDGET.step_limit, BUDGET.timeout_seconds, BUDGET.memory_limit_bytes,
                    list(programs), correction, validate or (lambda o: ([], [])))


def _validator(witness_required=True):
    return agent_tools.make_validator(OperationBridge(ROOT), ExecutionSandbox(), BUDGET, witness_required,
                                      _python_blocks, _parse_sandbox_witness, _witness_written_in_program)


def _call(name, args, cid):
    return {"type": "function_call", "name": name, "arguments": json.dumps(args), "call_id": cid}


class Script:
    def __init__(self, *replies):
        self.replies, self.requests = list(replies), []

    def __call__(self, body):
        self.requests.append(json.loads(json.dumps(body)))
        return {"output": self.replies.pop(0), "usage": {"input_tokens": 10, "output_tokens": 5}}


# ---- off by default: nothing changes

def test_off_by_default_no_request_carries_tools(tmp_path):
    engine, response, requests, events = _engine(tmp_path, lambda req: json.dumps(outcome(GOOD)), agent_tools_on=False)
    assert engine.agent_tools is False and response.closed
    assert all(r.tools is None for r in requests)
    assert not any(e["kind"] == "AGENT_TOOL_CALL" for e in events)


def test_the_prompt_is_the_same_with_tools_on(tmp_path):
    prompts = {}
    for on in (False, True):
        _, _, requests, _ = _engine(tmp_path / str(on), lambda req: json.dumps(outcome(GOOD)), agent_tools_on=on)
        prompts[on] = next(r.prompt for r in requests if r.operation == "EXECUTE_UNCONFIRMED")
    assert prompts[True] == prompts[False]  # the prompt hash, and so replay, are unchanged


# ---- on: the engine's tool host

def test_a_rejected_submission_is_corrected_in_the_call_and_the_host_verifies_the_accepted_one(tmp_path, monkeypatch):
    # A small step budget: the step limit, not the wall clock, stops the endless loop, however loaded the machine
    # (10 million traced steps can outlast the 30-second limit under parallel load). No prompt hash is compared here.
    from dataclasses import replace

    from pdl_taskmaster.verification import sandbox as sandbox_module

    for tier, budget in list(sandbox_module.EXECUTION_BUDGETS.items()):
        monkeypatch.setitem(sandbox_module.EXECUTION_BUDGETS, tier, replace(budget, step_limit=100_000))
    monkeypatch.setattr(sandbox_module, "DEFAULT_BUDGET", sandbox_module.EXECUTION_BUDGETS["STANDARD"])

    def execute(req):
        host = req.tools
        assert host.tool_names() == ["run_python", SUBMIT]  # no previous attempt: no read_attempt
        assert "steps used" in host.dispatch("run_python", json.dumps({"code": "print(6 * 7)"}))
        envelope, accepted = host.submit(json.dumps({"outcome": outcome(SLOW)}))
        assert accepted is None and envelope["errors"][0]["code"] == "STEP_BUDGET_EXCEEDED"
        envelope, accepted = host.submit(json.dumps({"outcome": outcome(GOOD)}))
        assert envelope["ok"] is True
        return json.dumps(accepted)

    engine, response, requests, events = _engine(tmp_path, execute, agent_tools_on=True)
    assert response.closed and engine.controller.state.stage == Stage.CLOSED_SUCCESS
    assert requests[0].tools.tool_names() == ["submit_bootstrap_analysis"]  # BOOTSTRAP: its submission only
    tool_events = [e["payload"] for e in events if e["kind"] == "AGENT_TOOL_CALL"]
    assert [(p["tool"], p.get("accepted")) for p in tool_events] == [("run_python", None), (SUBMIT, False), (SUBMIT, True)]
    kinds = [e["kind"] for e in events]
    assert "SANDBOX_RUN" in kinds and "VERIFICATION_PASSED" in kinds  # the host's own run and verification


def test_a_repair_reads_the_previous_attempt_as_the_host_ran_it(tmp_path):
    seen = []

    def execute(req):
        host = req.tools
        seen.append(host.tool_names())
        if len(seen) == 1:
            return json.dumps(outcome("raise ValueError('boom')"))
        text = host.read_attempt()
        assert "   1  raise ValueError('boom')" in text and "OPERATOR CORRECTION:" in text
        return json.dumps(outcome(GOOD))

    engine, response, _, _ = _engine(tmp_path, execute, agent_tools_on=True)
    assert seen == [["run_python", SUBMIT], ["read_attempt", "run_python", SUBMIT]]
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS


def test_the_tools_run_at_the_attempts_budget_in_the_session_sandbox(tmp_path):
    hosts = []
    _engine(tmp_path, lambda req: hosts.append(req.tools) or json.dumps(outcome(GOOD)), agent_tools_on=True)
    engine_budget = EXECUTION_BUDGETS["STANDARD"]
    assert (hosts[0].step_limit, hosts[0].timeout) == (engine_budget.step_limit, engine_budget.timeout_seconds)
    assert "step budget exceeded: True" in hosts[0].run_python(SLOW)


# ---- the API worker

def _request(tmp_path):
    captured = []
    _engine(tmp_path, lambda req: captured.append(req) or json.dumps(outcome(GOOD)), agent_tools_on=True)
    return captured[0]


def _worker(monkeypatch, replies, *, on):
    sent = []

    def fake_send(self, request, deadline):
        sent.append(json.loads(request.data.decode("utf-8")))
        return {"id": f"gen-{len(sent)}", "model": "m", "output": replies.pop(0),
                "usage": {"input_tokens": 10, "output_tokens": 5}}

    monkeypatch.setattr(ApiWorker, "_send_json_with_retries", fake_send)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    return ApiWorker(repo_root=ROOT, model="openai/gpt-oss-120b", agent_tools=on), sent


def test_attached_tools_override_worker_default_and_omitted_host_stays_plain(tmp_path, monkeypatch):
    request = _request(tmp_path)
    message = [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(outcome(GOOD))}]}]
    worker, sent = _worker(monkeypatch, [message, list(message)], on=False)
    tool_result = worker._call(request)
    import dataclasses
    plain_result = worker._call(dataclasses.replace(request, tools=None))
    assert sent[0]["tools"] and "text" not in sent[0]
    assert "tools" not in sent[1] and "text" in sent[1]
    assert json.loads(tool_result.text) == json.loads(plain_result.text) == outcome(GOOD)


def test_the_worker_with_tools_on_runs_the_loop(tmp_path, monkeypatch):
    request = _request(tmp_path)
    request.tools.validate = _validator()
    worker, sent = _worker(monkeypatch, [[_call("run_python", {"code": "print(1)"}, "c1")],
                                         [_call(SUBMIT, {"outcome": outcome(GOOD)}, "s1")]], on=True)
    result = worker._call(request)
    assert json.loads(result.text) == outcome(GOOD)
    assert result.metadata["tool_loop"]["final"] == "submitted" and result.metadata["usage"]["output_tokens"] == 10
    assert all("tools" in body and "text" not in body for body in sent)
    assert sent[0]["instructions"].endswith(request.tools.capability_note())


# ---- the loop

def test_tools_are_mcp_shaped_and_none_returns_a_verdict():
    assert [t["name"] for t in TOOLS] == ["read_attempt", "run_python", SUBMIT, "submit_execute",
                                         "submit_bootstrap_analysis", "submit_draft_prompt", "submit_draft_plan"]
    assert all(set(t) == {"name", "description", "inputSchema"} for t in TOOLS)
    text = json.dumps(TOOLS).lower().replace("verifies", "")
    assert "witness" not in text and "verif" not in text
    assert agent_tools.TOOL_OPERATIONS == ("EXECUTE_UNCONFIRMED", "EXECUTE", "BOOTSTRAP_ANALYSIS", "DRAFT_PROMPT",
                                           "DRAFT_PLAN")


def test_budgets_hold(tmp_path):
    host = _host(_validator())
    send = Script(*[[_call("run_python", {"code": "print(1)"}, f"c{i}")] for i in range(MAX_TOOL_CALLS + 1)],
                  [_call(SUBMIT, {"outcome": outcome(GOOD)}, "s1")])
    text, summary = run_loop({"model": "m", "input": "P", "text": {"format": {"type": "json_object"}}}, send, host)
    assert summary["final"] == "submitted" and host.work_calls() == MAX_TOOL_CALLS
    refused = [i for i in send.requests[-1]["input"] if i.get("type") == "function_call_output"
               and "budget is spent" in i["output"]]
    assert len(refused) == 1


def test_a_spent_loop_never_returns_a_submission_the_wire_model_rejected():
    host = _host(_validator())
    bad = {"kind": "NOPE"}
    send = Script(*[[_call(SUBMIT, {"outcome": bad}, f"s{i}")] for i in range(MAX_SUBMISSIONS)],
                  [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(outcome(GOOD))}]}])
    text, summary = run_loop({"model": "m", "input": "P", "text": {"format": {"type": "json_object"}}}, send, host)
    assert summary["final"] == "formatted" and send.requests[-1]["text"] == {"format": {"type": "json_object"}}


def test_an_outcome_sent_unwrapped_or_wrapped_twice_is_the_outcome():
    host = _host(_validator())
    assert host.submit(json.dumps(outcome(GOOD)))[1] == outcome(GOOD)
    assert host.submit(json.dumps({"outcome": {"outcome": outcome(GOOD)}}))[1] == outcome(GOOD)


@pytest.mark.parametrize("body,code", [('WITNESS: {"polarity": "positive", "data": {"x": 42}}', "WITNESS_NOT_PRINTED"),
                                       ("The answer is 42.", "NO_PROGRAM"),
                                       ("raise ValueError('x')", "PROGRAM_FAILED")])
def test_the_submission_check_is_the_hosts_structural_check(body, code):
    errors, _ = _validator()(outcome(body))
    assert errors[0]["code"] == code


# ---- the submit-only operations (the user's decision: every measured loop)

ANALYSIS = {"kind": "ANALYSIS", "task_summary": "Count the subsets of 1..10 that sum to 20.", "approach_notes": "",
            "risk_notes": "", "task_entities": [{"surface": "20", "kind": "parameter", "status": "given"}]}


def test_bootstrap_submissions_are_checked_by_the_wire_model_and_a_wire_retry_gets_a_fresh_host(tmp_path):
    hosts = []

    def model_call(req):
        if req.operation == "BOOTSTRAP_ANALYSIS":
            hosts.append(req.tools)
            if len(hosts) == 1:
                bad = {**ANALYSIS, "task_entities": [{"surface": "20", "kind": "task", "status": "given"}]}
                envelope, accepted = req.tools.submit(json.dumps({"outcome": bad}))
                assert accepted is None and envelope["errors"][0]["path"].endswith("task_entities.0.kind")
                return json.dumps(bad)  # a spent loop would never return this; here it exercises the wire retry
            return json.dumps(req.tools.submit(json.dumps({"outcome": ANALYSIS}))[1])
        return json.dumps(outcome(GOOD))

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=Sys1("VERIFIED_EXECUTION"),
                           no_review=True)
    engine.agent_tools = True
    engine.handle_user_message("Count the subsets of 1..10 that sum to 20.")
    assert len(hosts) == 2 and hosts[0] is not hosts[1] and len(hosts[1].submissions) == 1
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS


def test_draft_submissions_are_checked_by_the_lint(tmp_path):
    from test_execution_phase import PLAN, PROMPT, _ir

    seen = {}

    def model_call(req):
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return _bootstrap()
        if req.operation == "DRAFT_PROMPT":
            host = req.tools
            seen["prompt"] = host.tool_names()
            fielded = {"kind": "PROMPT", "prompt_body": "TASK: solve it\n" + PROMPT, "approach_handoff": "NONE"}
            envelope, _ = host.submit(json.dumps({"outcome": fielded}))
            seen["codes"] = [e["code"] for e in envelope["errors"]]
            clean = {"kind": "PROMPT", "prompt_body": PROMPT, "approach_handoff": "NONE"}
            return json.dumps(host.submit(json.dumps({"outcome": clean}))[1])
        if req.operation == "DRAFT_PLAN":
            seen["plan"] = req.tools.tool_names()
            return json.dumps(req.tools.submit(json.dumps({"outcome": {"neutral_plan_body": PLAN}}))[1])
        if req.operation == "EXECUTE":
            assert req.tools is None  # L168: the confirmed route's EXECUTE has its loop only when asked
            return json.dumps({"kind": "RESULT", "body": "42", "result_ir": _ir()})
        raise AssertionError(req.operation)

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=Sys1())
    engine.agent_tools = True
    engine.handle_user_message("$confirm-with-pseudocode Solve the stated task.")
    engine.handle_user_message("/confirm")
    engine.handle_user_message("/confirm")
    assert seen == {"prompt": ["submit_draft_prompt"], "codes": ["PDL_LINT"], "plan": ["submit_draft_plan"]}
    kinds = [e["kind"] for e in engine.workspace.read_events()]
    assert "PROMPT_LINT_RETRY" not in kinds  # the lint found nothing after the call: it was met inside it
