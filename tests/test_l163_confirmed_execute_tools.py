"""L163, ADR-0029 amendment: the confirmed route's EXECUTE gets EXECUTE_UNCONFIRMED's in-call tools (run_python,
read_attempt on a repair, and its own checked submission, submit_execute). The submission is checked by EXECUTE's
wire model and the host's program checks; the host verifies the accepted reply as any reply. Offline: the worker is
scripted."""
from __future__ import annotations

import json

from pdl_taskmaster.controller.mechanical_controller import Stage
from pdl_taskmaster.runtime.agent_tools import SUBMIT_EXECUTE
from pdl_taskmaster.runtime.session_engine import SessionEngine

from test_agent_tools import GOOD, outcome
from test_execution_phase import PLAN, PROMPT, ROOT, ClassifyingSys1, _ir


def _confirmed(tmp_path, execute, *, agent_tools_on: bool, problem_class: str = "VERIFIED_EXECUTION"):
    requests: list = []

    def model_call(req):
        requests.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({"kind": "ANALYSIS", "task_summary": "The user states a task to solve.",
                               "approach_notes": "", "risk_notes": "", "task_entities": []})
        if req.operation == "DRAFT_PROMPT":
            return json.dumps({"kind": "PROMPT", "prompt_body": PROMPT, "approach_handoff": "NONE"})
        if req.operation == "DRAFT_PLAN":
            return json.dumps({"neutral_plan_body": PLAN})
        if req.operation == "EXECUTE":
            return execute(req)
        raise AssertionError(req.operation)

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=ClassifyingSys1(problem_class))
    engine.agent_tools = agent_tools_on
    engine.handle_user_message("$confirm-with-pseudocode Solve the stated task.")
    engine.handle_user_message("/confirm")
    engine.handle_user_message("/confirm")
    executes = [r for r in requests if r.operation == "EXECUTE"]
    return engine, executes, list(engine.workspace.read_events())


def _result(body: str) -> dict:
    return {"kind": "RESULT", "body": body, "result_ir": _ir()}


def test_execute_submissions_are_checked_by_executes_wire_model_and_the_host_verifies_the_accepted_one(tmp_path):
    def execute(req):
        host = req.tools
        assert host.tool_names() == ["run_python", SUBMIT_EXECUTE]  # no previous attempt: no read_attempt
        envelope, accepted = host.submit(json.dumps({"outcome": outcome(GOOD)}))  # EXECUTE_UNCONFIRMED's shape
        assert accepted is None and {e["code"] for e in envelope["errors"]} == {"OUTPUT_MALFORMED"}
        envelope, accepted = host.submit(json.dumps({"outcome": _result(GOOD)}))
        assert envelope["ok"] is True
        return json.dumps(accepted)

    engine, executes, events = _confirmed(tmp_path, execute, agent_tools_on=True)
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS
    calls = [e["payload"] for e in events if e["kind"] == "AGENT_TOOL_CALL" and e["payload"]["tool"] == SUBMIT_EXECUTE]
    assert [(c["operation"], c["accepted"]) for c in calls] == [("EXECUTE", False), ("EXECUTE", True)]
    assert "VERIFICATION_PASSED" in [e["kind"] for e in events]  # the host's own run and verification


def test_a_confirmed_repair_reads_the_previous_execute_attempt(tmp_path):
    seen = []

    def execute(req):
        seen.append(req.tools.tool_names())
        if len(seen) == 1:
            return json.dumps(_result("raise ValueError('boom')"))
        text = req.tools.read_attempt()
        assert "   1  raise ValueError('boom')" in text and "OPERATOR CORRECTION" in text
        assert req.tools.attempt == 2
        return json.dumps(_result(GOOD))

    engine, _, _ = _confirmed(tmp_path, execute, agent_tools_on=True)
    assert seen == [["run_python", SUBMIT_EXECUTE], ["read_attempt", "run_python", SUBMIT_EXECUTE]]
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS


def test_tools_off_execute_carries_none_and_its_prompt_is_the_same_either_way(tmp_path):
    prompts = {}
    for on in (False, True):
        _, executes, _ = _confirmed(tmp_path / str(on), lambda req: json.dumps(_result(GOOD)), agent_tools_on=on)
        assert (executes[0].tools is not None) is on
        prompts[on] = executes[0].prompt
    assert prompts[True] == prompts[False]  # the prompt hash, and so replay, are unchanged
