"""TOOL_EXTRACTION_PLAN.md step 6: the in-call agent tools served over MCP stdio. The server is a thin adapter: the
schemas, outputs, budgets and submission check are runtime/agent_tools.py's. Offline; one test runs the real server
process over stdio."""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from pdl_taskmaster.host import mcp_server
from pdl_taskmaster.runtime import agent_tools
from pdl_taskmaster.runtime.agent_tools import SUBMIT

ROOT = Path(__file__).resolve().parents[1]
GOOD = "import json\nprint('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'x': 6 * 7}}))"  # computed (L139)
IR = {"files": [], "reconciliation": [], "open_defects": []}


def outcome(body: str) -> dict:
    return {"kind": "RESULT", "interpretation": "i", "approach": "a", "body": body, "result_ir": IR}


def _server(witness_required: bool = True, version: str | None = mcp_server.PROTOCOL_VERSION,
            sessions: Path | None = None) -> mcp_server.AgentToolServer:
    """A server after initialize at ``version`` (None: before initialize)."""
    server = mcp_server.AgentToolServer(mcp_server.build_host("STANDARD", witness_required, repo_root=ROOT),
                                        mcp_server.ClosedSessions(sessions) if sessions else None)
    if version is not None:
        assert _rpc(server, "initialize", {"protocolVersion": version, "capabilities": {},
                                           "clientInfo": {"name": "t", "version": "0"}})["result"]
    return server


def _rpc(server, method, params=None, mid=1):
    return server.handle({"jsonrpc": "2.0", "id": mid, "method": method, "params": params or {}})


def test_initialize_names_the_tools_capability_and_states_the_budgets():
    result = _rpc(_server(version=None), "initialize", {"protocolVersion": mcp_server.PROTOCOL_VERSION, "capabilities": {},
                                            "clientInfo": {"name": "t", "version": "0"}})["result"]
    assert result["protocolVersion"] == mcp_server.PROTOCOL_VERSION
    assert result["capabilities"] == {"tools": {"listChanged": False}}
    assert result["instructions"].startswith("TOOLS FOR THIS CALL: run_python and submit_execute_unconfirmed")


def test_tools_list_serves_the_registry_definitions_unchanged():
    tools = _rpc(_server(), "tools/list")["result"]["tools"]
    registry = [t for t in agent_tools.TOOLS if t["name"] in ("run_python", SUBMIT)]  # no previous attempt
    assert [t["name"] for t in tools] == [t["name"] for t in registry]
    assert tools[0] == registry[0] and tools[1]["inputSchema"] == registry[1]["inputSchema"]
    # L121 E-2: outside the harness nothing verifies an accepted submission, and the description says so.
    assert agent_tools.VERIFIED_AFTER_ACCEPTANCE not in tools[1]["description"]
    assert tools[1]["description"].endswith(mcp_server.MCP_AFTER_ACCEPTANCE)


def test_run_python_returns_the_hosts_output_and_holds_its_budget():
    server = _server()
    result = _rpc(server, "tools/call", {"name": "run_python", "arguments": {"code": "print(6 * 7)"}})["result"]
    assert result["isError"] is False and "standard output:\n42" in result["content"][0]["text"]
    for _ in range(agent_tools.MAX_TOOL_CALLS - 1):
        _rpc(server, "tools/call", {"name": "run_python", "arguments": {"code": "print(1)"}})
    spent = _rpc(server, "tools/call", {"name": "run_python", "arguments": {"code": "print(1)"}})["result"]
    assert spent["isError"] is True and "budget is spent" in spent["content"][0]["text"]


def test_a_submission_is_checked_structurally_and_never_returns_a_verdict():
    server = _server()
    rejected = _rpc(server, "tools/call", {"name": SUBMIT, "arguments": {"outcome": outcome("The answer is 42.")}})
    assert rejected["result"]["isError"] is True
    assert rejected["result"]["structuredContent"]["errors"][0]["code"] == "NO_PROGRAM"
    accepted = _rpc(server, "tools/call", {"name": SUBMIT, "arguments": {"outcome": outcome(GOOD)}})["result"]
    assert accepted["isError"] is False
    assert accepted["structuredContent"]["result"] == mcp_server.MCP_ACCEPTED
    assert "verified" not in json.dumps(accepted).lower()


def test_unknown_methods_and_tools_notifications_and_bad_json():
    server = _server()
    assert _rpc(server, "tools/call", {"name": "read_attempt", "arguments": {}})["error"]["code"] == -32602
    assert _rpc(server, "resources/list")["error"]["code"] == -32601
    assert server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    out = io.StringIO()
    mcp_server.serve(server, io.StringIO("not json\n\n"), out)
    assert json.loads(out.getvalue())["error"]["code"] == -32700


def test_the_server_process_speaks_mcp_over_stdio(tmp_path):
    lines = [{"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": mcp_server.PROTOCOL_VERSION, "capabilities": {},
                         "clientInfo": {"name": "t", "version": "0"}}},
             {"jsonrpc": "2.0", "method": "notifications/initialized"},
             {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
             {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
              "params": {"name": "run_python", "arguments": {"code": "print(sum(range(10)))"}}}]
    proc = subprocess.run([sys.executable, "-m", "pdl_taskmaster.host.mcp_server", "--sessions", str(tmp_path),
                           "--log", str(tmp_path / "calls.jsonl")], cwd=ROOT,  # nothing written into the repo
                          input="".join(json.dumps(m) + "\n" for m in lines), capture_output=True, text=True,
                          encoding="utf-8", timeout=120,
                          env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
    responses = [json.loads(x) for x in proc.stdout.splitlines() if x.strip()]
    assert [r["id"] for r in responses] == [1, 2, 3]
    assert [t["name"] for t in responses[1]["result"]["tools"]] == ["run_python", SUBMIT]
    assert "standard output:\n45" in responses[2]["result"]["content"][0]["text"]


def test_a_byte_order_mark_before_the_first_request_is_ignored(tmp_path):
    # Windows PowerShell puts one before text it pipes to a program when its console is set to UTF-8.
    lines = [{"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": mcp_server.PROTOCOL_VERSION, "capabilities": {},
                         "clientInfo": {"name": "t", "version": "0"}}},
             {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]
    proc = subprocess.run([sys.executable, "-m", "pdl_taskmaster.host.mcp_server", "--sessions", str(tmp_path),
                           "--log", str(tmp_path / "calls.jsonl")], cwd=ROOT,
                          input=b"\xef\xbb\xbf" + "".join(json.dumps(m) + "\n" for m in lines).encode("utf-8"),
                          capture_output=True, timeout=120, env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
    responses = [json.loads(x) for x in proc.stdout.decode("utf-8").splitlines() if x.strip()]
    assert [r.get("id") for r in responses] == [1, 2], responses
    assert all("error" not in r for r in responses), responses


# L138: lifecycle, protocol versions, tool-level and protocol-level failures, the result schema, batches.

@pytest.mark.parametrize("asked, answered", [(v, v) for v in mcp_server.SUPPORTED_PROTOCOL_VERSIONS] + [
    ("2026-07-28", "2025-11-25"),  # the stateless revision has no initialize handshake: never echoed
    ("2099-01-01", "2025-11-25"), ("2024-10-07", "2025-11-25"), (None, "2025-11-25")])
def test_initialize_echoes_a_supported_version_and_offers_the_newest_otherwise(asked, answered):
    server = _server(version=None)
    result = _rpc(server, "initialize", {"protocolVersion": asked, "capabilities": {}})["result"]
    assert result["protocolVersion"] == answered == server.protocol_version
    assert mcp_server.SUPPORTED_PROTOCOL_VERSIONS[0] == mcp_server.PROTOCOL_VERSION == "2025-11-25"


def test_nothing_is_served_before_initialize_but_ping(tmp_path, monkeypatch):
    server = _server(version=None, sessions=tmp_path)
    monkeypatch.setattr(server.host.sandbox, "run_code", lambda *a, **k: pytest.fail("a program ran"))
    for method, params in (("tools/list", {}), ("tools/call", {"name": "run_python", "arguments": {"code": "1"}}),
                           ("tools/call", {"name": SUBMIT, "arguments": {"outcome": outcome(GOOD)}}),
                           ("resources/list", {}), ("resources/read", {"uri": "pdlt://sessions/x"})):
        error = _rpc(server, method, params)["error"]
        assert error["code"] == mcp_server.INVALID_REQUEST and "not initialized" in error["message"], method
    assert server.host.calls == [] and server.host.submissions == []
    assert _rpc(server, "ping")["result"] == {}
    assert _rpc(server, "no/such/method")["error"]["code"] == -32601


def test_a_second_initialize_is_refused_and_a_spent_budget_stays_spent():
    server = _server()
    for _ in range(agent_tools.MAX_SUBMISSIONS):
        _rpc(server, "tools/call", {"name": SUBMIT, "arguments": {"outcome": outcome("No program.")}})
    again = _rpc(server, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {}})
    assert again["error"]["code"] == mcp_server.INVALID_REQUEST and "already initialized" in again["error"]["message"]
    assert server.protocol_version == mcp_server.PROTOCOL_VERSION
    spent = _rpc(server, "tools/call", {"name": SUBMIT, "arguments": {"outcome": outcome(GOOD)}})["result"]
    assert spent["isError"] is True and "submission budget is spent" in spent["content"][0]["text"]
    assert len(server.host.submissions) == agent_tools.MAX_SUBMISSIONS


def test_tool_failures_are_results_with_is_error():
    server = _server()
    extra = _rpc(server, "tools/call", {"name": "run_python", "arguments": {"code": "print(1)", "timeout": 9}})
    assert "error" not in extra and extra["result"]["isError"] is True
    assert "do not match run_python's input schema" in extra["result"]["content"][0]["text"]
    malformed = _rpc(server, "tools/call", {"name": SUBMIT, "arguments": {"outcome": "not an object"}})["result"]
    assert malformed["isError"] is True and malformed["structuredContent"]["errors"][0]["code"] == "OUTPUT_MALFORMED"
    for _ in range(agent_tools.MAX_TOOL_CALLS):
        _rpc(server, "tools/call", {"name": "run_python", "arguments": {"code": "print(1)"}})
    spent = _rpc(server, "tools/call", {"name": "run_python", "arguments": {"code": "print(1)"}})
    assert "error" not in spent and spent["result"]["isError"] is True


def test_protocol_failures_are_json_rpc_errors():
    server = _server()
    assert server.handle({"jsonrpc": "2.0", "id": None, "method": "ping"}) == {
        "jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "a request id must be a string or an integer"}}
    assert server.handle({"jsonrpc": "2.0", "id": True, "method": "ping"})["error"]["code"] == -32600
    assert server.handle({"jsonrpc": "2.0", "id": "a", "method": "ping"})["result"] == {}
    assert server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": [1]})["error"]["code"] == -32602
    assert _rpc(server, "no/such/method")["error"]["code"] == -32601
    assert _rpc(server, "tools/call", {"name": "no_such_tool", "arguments": {}})["error"]["code"] == -32602
    out = io.StringIO()
    mcp_server.serve(server, io.StringIO("{not json\n42\n\"text\"\n"), out)
    assert [json.loads(line)["error"]["code"] for line in out.getvalue().splitlines()] == [-32700, -32600, -32600]


def _envelopes():
    host = mcp_server.build_host("STANDARD", True, repo_root=ROOT)
    found = [host.submit(json.dumps({"outcome": outcome(GOOD)}))[0],
             host.submit(json.dumps({"outcome": outcome("No program.")}))[0],
             host.submit("not json")[0]]
    host = mcp_server.build_host("STANDARD", True, repo_root=ROOT)
    found += [host.submit(json.dumps({"outcome": outcome(GOOD), "note": "x"}))[0],
              host.submit(json.dumps({"outcome": []}))[0]]
    return found


def test_every_submission_result_conforms_to_the_published_schema():
    Draft202012Validator.check_schema(agent_tools.SUBMIT_RESULT_SCHEMA)
    validator = Draft202012Validator(agent_tools.SUBMIT_RESULT_SCHEMA)
    envelopes = _envelopes()
    assert [e["ok"] for e in envelopes] == [True, False, False, False, False]
    assert [e["submissions_left"] for e in envelopes[1:]] == [1, 0, 2, 1]
    for envelope in envelopes:
        validator.validate(envelope)
    server = _server()
    for body in ("No program.", GOOD):
        validator.validate(_rpc(server, "tools/call", {"name": SUBMIT,
                                                       "arguments": {"outcome": outcome(body)}})["result"]["structuredContent"])
    accepted, rejected = envelopes[0], envelopes[1]
    for wrong in ({**accepted, "errors": rejected["errors"]}, {**accepted, "verdict": "PASS"},
                  {k: v for k, v in rejected.items() if k != "submissions_left"}, {**rejected, "errors": []},
                  {**rejected, "ok": True}, {**rejected, "submissions_left": -1}):
        assert not validator.is_valid(wrong), wrong


@pytest.mark.parametrize("version, structured", [("2024-11-05", False), ("2025-03-26", False),
                                                 ("2025-06-18", True), ("2025-11-25", True)])
def test_output_schema_and_structured_content_follow_the_negotiated_version(version, structured):
    server = _server(version=version)
    submit = next(t for t in _rpc(server, "tools/list")["result"]["tools"] if t["name"] == SUBMIT)
    assert ("outputSchema" in submit) is structured
    result = _rpc(server, "tools/call", {"name": SUBMIT, "arguments": {"outcome": outcome(GOOD)}})["result"]
    assert ("structuredContent" in result) is structured
    assert json.loads(result["content"][0]["text"])["ok"] is True  # the text carries the envelope either way


def _call(mid, code="print(1)"):
    return {"jsonrpc": "2.0", "id": mid, "method": "tools/call",
            "params": {"name": "run_python", "arguments": {"code": code}}}


def test_a_batch_under_2025_03_26_answers_its_requests_in_order():
    server = _server(version="2025-03-26")
    note = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    responses = server.handle_batch([_call(1, "print(6 * 7)"), note, {"jsonrpc": "2.0", "id": 2, "method": "ping"},
                                     7])
    assert [r["id"] for r in responses] == [1, 2, None]
    assert "standard output:\n42" in responses[0]["result"]["content"][0]["text"]
    assert responses[2]["error"]["code"] == -32600  # an element that is not an object gets its own error
    assert server.handle_batch([note, note]) is None
    over = server.handle_batch([_call(i) for i in range(3, 3 + agent_tools.MAX_TOOL_CALLS)])
    assert over[-1]["result"]["isError"] is True and "budget is spent" in over[-1]["result"]["content"][0]["text"]
    out = io.StringIO()
    mcp_server.serve(server, io.StringIO(json.dumps([{"jsonrpc": "2.0", "id": 9, "method": "ping"}]) + "\n"), out)
    assert json.loads(out.getvalue()) == [{"jsonrpc": "2.0", "id": 9, "result": {}}]


@pytest.mark.parametrize("version, batch, problem", [
    (None, [{"jsonrpc": "2.0", "id": 1, "method": "ping"}], "not initialized"),
    ("2024-11-05", [{"jsonrpc": "2.0", "id": 1, "method": "ping"}], "has no batches"),
    ("2025-06-18", [{"jsonrpc": "2.0", "id": 1, "method": "ping"}], "has no batches"),
    ("2025-11-25", [{"jsonrpc": "2.0", "id": 1, "method": "ping"}], "has no batches"),
    ("2025-03-26", [], "empty"),
    ("2025-03-26", [{"jsonrpc": "2.0", "id": i, "method": "ping"} for i in range(mcp_server.MAX_BATCH + 1)],
     "at most"),
    ("2025-03-26", [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}, _call(2)], "initialize"),
])
def test_a_batch_is_refused_whole_and_nothing_in_it_runs(version, batch, problem, monkeypatch):
    server = _server(version=version)
    monkeypatch.setattr(server.host.sandbox, "run_code", lambda *a, **k: pytest.fail("a program ran"))
    response = server.handle_batch(batch)
    assert response["id"] is None and response["error"]["code"] == -32600 and problem in response["error"]["message"]
    assert server.host.calls == []


def test_main_closes_the_log_and_the_sandbox(tmp_path, monkeypatch):
    closed = []
    built = mcp_server.build_host

    def build(*args, **kwargs):
        host = built(*args, **kwargs)
        close = host.sandbox.close
        host.sandbox.close = lambda: (closed.append("sandbox"), close())[1]
        return host

    class Log(mcp_server.CallLog):
        def close(self):
            closed.append("log")
            super().close()

    monkeypatch.setattr(mcp_server, "build_host", build)
    monkeypatch.setattr(mcp_server, "CallLog", Log)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}) + "\n"))
    monkeypatch.setattr("sys.stdout", io.StringIO())
    assert mcp_server.main(["--sessions", str(tmp_path), "--log", str(tmp_path / "calls.jsonl")]) == 0
    assert closed == ["sandbox", "log"]
