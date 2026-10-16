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

from pdl_taskmaster.host import mcp_server
from pdl_taskmaster.runtime import agent_tools
from pdl_taskmaster.runtime.agent_tools import SUBMIT

ROOT = Path(__file__).resolve().parents[1]
GOOD = "import json\nprint('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'x': 42}}))"
IR = {"files": [], "reconciliation": [], "open_defects": []}


def outcome(body: str) -> dict:
    return {"kind": "RESULT", "interpretation": "i", "approach": "a", "body": body, "result_ir": IR}


def _server(witness_required: bool = True) -> mcp_server.AgentToolServer:
    return mcp_server.AgentToolServer(mcp_server.build_host("STANDARD", witness_required, repo_root=ROOT))


def _rpc(server, method, params=None, mid=1):
    return server.handle({"jsonrpc": "2.0", "id": mid, "method": method, "params": params or {}})


def test_initialize_names_the_tools_capability_and_states_the_budgets():
    result = _rpc(_server(), "initialize", {"protocolVersion": mcp_server.PROTOCOL_VERSION, "capabilities": {},
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


def test_the_server_process_speaks_mcp_over_stdio():
    lines = [{"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": mcp_server.PROTOCOL_VERSION, "capabilities": {},
                         "clientInfo": {"name": "t", "version": "0"}}},
             {"jsonrpc": "2.0", "method": "notifications/initialized"},
             {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
             {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
              "params": {"name": "run_python", "arguments": {"code": "print(sum(range(10)))"}}}]
    proc = subprocess.run([sys.executable, "-m", "pdl_taskmaster.host.mcp_server"], cwd=ROOT,
                          input="".join(json.dumps(m) + "\n" for m in lines), capture_output=True, text=True,
                          encoding="utf-8", timeout=120,
                          env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
    responses = [json.loads(x) for x in proc.stdout.splitlines() if x.strip()]
    assert [r["id"] for r in responses] == [1, 2, 3]
    assert [t["name"] for t in responses[1]["result"]["tools"]] == ["run_python", SUBMIT]
    assert "standard output:\n45" in responses[2]["result"]["content"][0]["text"]
