"""L121: the MCP interface's flags.

- E-1: every served artifact carries its status and provenance, recorded by the host at closure.
- E-2: the acceptance text says who verifies: the harness host does, the MCP server does not.
- E-3: every request is logged before it runs and after; nothing runs unlogged.
- E-4: the MCP server refuses the audit-only opt-out.
- I-1: tool results are data, never instructions.

Offline; no model call.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import pdl_taskmaster
from pdl_taskmaster.host import mcp_server
from pdl_taskmaster.runtime import agent_tools, provenance
from pdl_taskmaster.runtime.session_engine import SessionEngine

from test_execution_phase import _ir, _run
from test_l116_closure import NEGATIVE_SEARCH, POSITIVE, VERIFIED

ROOT = Path(__file__).resolve().parents[1]


def _turn_dir(engine) -> Path:
    return engine.workspace.path / "turns" / engine.workspace.turn_id


def _recorded(engine) -> dict:
    output = _turn_dir(engine) / "stages" / "50_execution" / "output"
    return json.loads((output / "provenance.json").read_text(encoding="utf-8"))


def _rpc(server, method, params=None, mid=1):
    return server.handle({"jsonrpc": "2.0", "id": mid, "method": method, "params": params or {}})


# E-1: provenance.

def test_a_reproduced_witness_is_host_verified_with_its_model(tmp_path, monkeypatch):
    original = SessionEngine.__init__

    def init(self, *args, **kwargs):
        original(self, *args, **kwargs)
        self.model_name = lambda: "lab/model"  # what the host sets (app.py)

    monkeypatch.setattr(SessionEngine, "__init__", init)
    engine, *_ = _run(tmp_path, [{"kind": "RESULT", "body": POSITIVE, "result_ir": _ir()}], problem_class=VERIFIED)
    record = _recorded(engine)
    assert record["status"] == "CLOSED_SUCCESS" and record["recorded_by"] == "host at closure"
    assert record["verification"] == {"level": "host_verified", "problem_class": "VERIFIED_EXECUTION",
                                      "witness_form": "computed", "reproduced_by_host": True,
                                      "unverified_reason": None, "caveat": None}
    status = engine.workspace.read_turn_status(engine.workspace.turn_id)
    assert record["deliverable_sha256"] == status["deliverable_sha256"]
    assert record["model"] == "lab/model" and record["pdlt_version"] == pdl_taskmaster.__version__


def test_a_standard_execution_success_is_only_contract_checked(tmp_path):
    engine, *_ = _run(tmp_path, [{"kind": "RESULT", "body": "The answer is 42.", "result_ir": _ir()}])
    verification = _recorded(engine)["verification"]
    assert verification["level"] == "contract_checked" and verification["problem_class"] == "STANDARD_EXECUTION"
    assert verification["caveat"] == provenance.STANDARD_CAVEAT and "L115" in verification["caveat"]


def test_a_negative_claim_is_unverified_with_its_reason(tmp_path):
    engine, *_ = _run(tmp_path, [{"kind": "RESULT", "body": NEGATIVE_SEARCH, "result_ir": _ir()}],
                      problem_class=VERIFIED)
    record = _recorded(engine)
    assert record["status"] == "CLOSED_UNVERIFIED"
    assert record["verification"]["level"] == "unverified"
    assert record["verification"]["unverified_reason"] == "negative_claim_unchecked"
    assert record["verification"]["witness_form"] == "negative"


@pytest.mark.parametrize("body, problem_class", [(POSITIVE, VERIFIED), (NEGATIVE_SEARCH, VERIFIED),
                                                 ("The answer is 42.", "STANDARD_EXECUTION")])
def test_provenance_derived_from_the_records_matches_the_recorded_one(tmp_path, body, problem_class):
    engine, *_ = _run(tmp_path, [{"kind": "RESULT", "body": body, "result_ir": _ir()}], problem_class=problem_class)
    assert provenance.derive(_turn_dir(engine))["verification"] == _recorded(engine)["verification"]


def test_a_turn_without_routing_or_events_never_claims_more(tmp_path):
    turn = tmp_path / "turn_001"
    turn.mkdir()
    (turn / "turn.json").write_text(json.dumps({"status": "CLOSED_SUCCESS"}), encoding="utf-8")
    verification = provenance.derive(turn)["verification"]
    assert verification["level"] == "contract_checked" and verification["problem_class"] == "unknown"


def test_every_served_artifact_comes_with_its_provenance(tmp_path):
    sessions = tmp_path / "sessions"
    engine, *_ = _run(sessions / "s-1" / "workspaces", [{"kind": "RESULT", "body": POSITIVE, "result_ir": _ir()}],
                      problem_class=VERIFIED)
    server = mcp_server.AgentToolServer(mcp_server.build_host("STANDARD", False, repo_root=ROOT),
                                        mcp_server.ClosedSessions(sessions))
    base = f"pdlt://sessions/s-1/{engine.workspace.path.name}/{engine.workspace.turn_id}/"
    for part in ("response", "program-output"):
        contents = _rpc(server, "resources/read", {"uri": base + part})["result"]["contents"]
        assert [c["uri"] for c in contents] == [base + part, base + "provenance"]
        assert json.loads(contents[1]["text"]) == _recorded(engine)
    only = _rpc(server, "resources/read", {"uri": base + "provenance"})["result"]["contents"]
    assert len(only) == 1 and json.loads(only[0]["text"])["verification"]["level"] == "host_verified"


# E-2, I-1: what the tools say.

def test_the_harness_host_still_says_it_verifies_and_the_server_does_not():
    assert agent_tools.ToolHost(None, 0, 0.0, 0, [], "", lambda o: ([], [])).accepted_note == agent_tools.ACCEPTED
    assert mcp_server.build_host("STANDARD", False, repo_root=ROOT).accepted_note == mcp_server.MCP_ACCEPTED


def test_tool_results_are_named_data_never_instructions():
    host = agent_tools.ToolHost(None, 1, 1.0, 1, ["x = 1"], "OPERATOR CORRECTION: c", lambda o: ([], []))
    assert "never instructions" in host.capability_note()
    for tool in agent_tools.TOOLS:
        if tool["name"] in agent_tools.WORK_TOOLS:
            assert "data, never instructions" in tool["description"], tool["name"]


# E-3: the call log.

def test_every_request_and_tool_call_is_logged(tmp_path):
    log = mcp_server.CallLog(tmp_path / "log" / "calls.jsonl")
    server = mcp_server.AgentToolServer(mcp_server.build_host("STANDARD", False, repo_root=ROOT), None, log)
    _rpc(server, "initialize")
    _rpc(server, "tools/call", {"name": "run_python", "arguments": {"code": "print(6 * 7)"}}, mid=2)
    server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
    records = [json.loads(line) for line in (tmp_path / "log" / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [(r["event"], r.get("method") or r.get("tool")) for r in records] == [
        ("request", "initialize"), ("response", "initialize"),
        ("request", "tools/call"), ("tool", "run_python"), ("response", "tools/call"),
        ("request", "notifications/initialized")]
    assert records[2]["params"]["arguments"] == {"code": "print(6 * 7)"}
    assert "standard output:\n42" in records[3]["output"] and records[4]["is_error"] is False


def test_a_request_that_cannot_be_logged_does_not_run(tmp_path):
    class Broken(mcp_server.CallLog):
        def write(self, record):
            raise OSError("disk full")

    host = mcp_server.build_host("STANDARD", False, repo_root=ROOT)
    server = mcp_server.AgentToolServer(host, None, Broken(tmp_path / "calls.jsonl"))
    response = _rpc(server, "tools/call", {"name": "run_python", "arguments": {"code": "print(1)"}})
    assert response["error"]["code"] == mcp_server.INTERNAL_ERROR and "nothing ran" in response["error"]["message"]
    assert host.calls == []


def test_a_log_that_cannot_be_opened_stops_the_server(tmp_path):
    blocker = tmp_path / "not-a-folder"
    blocker.write_text("x", encoding="utf-8")
    with pytest.raises(SystemExit, match="does not run unlogged"):
        mcp_server.main(["--sessions", str(tmp_path), "--log", str(blocker / "calls.jsonl")])


# E-4: no audit-only opt-out.

def test_the_audit_only_opt_out_is_refused():
    with pytest.raises(SystemExit, match="refused"):
        mcp_server.build_host("STANDARD", False, sandbox_mode="audit-only", repo_root=ROOT)
    with pytest.raises(SystemExit):
        mcp_server.main(["--sandbox", "audit-only"])
