"""L123: the MCP server as an outside client sees it. The real server process is started over stdio and driven by
the official MCP Python SDK's client, so these tests check interoperability as well as behaviour: the handshake,
the published tool schemas, tool calls and their errors, budgets, the read-only resources with their provenance, the
call log, and the refused sandbox opt-out. Offline: no model call; programs run in the confined sandbox."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import anyio
import pytest
from jsonschema import Draft202012Validator
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp import MCPError as McpError

from pdl_taskmaster.host import mcp_server
from pdl_taskmaster.runtime import agent_tools

from test_execution_phase import _ir, _run
from test_l116_closure import POSITIVE, VERIFIED

ROOT = Path(__file__).resolve().parents[1]
GOOD = "import json\nprint('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'x': 6 * 7}}))"


def _outcome(body: str) -> dict:
    return {"kind": "RESULT", "interpretation": "i", "approach": "a", "body": body,
            "result_ir": {"files": [], "reconciliation": [], "open_defects": []}}


def _params(sessions: Path, log: Path, *extra: str) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "pdl_taskmaster.host.mcp_server", "--sessions", str(sessions), "--log", str(log), *extra],
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")}, cwd=str(ROOT))


def _session(sessions: Path, log: Path, body, *extra: str):
    async def main():
        async with stdio_client(_params(sessions, log, *extra)) as (read, write):
            async with ClientSession(read, write) as client:
                return await body(client)

    return anyio.run(main)


def _text(result) -> str:
    return "".join(getattr(item, "text", "") for item in result.content)


@pytest.fixture(scope="module")
def sessions(tmp_path_factory) -> tuple[Path, str]:
    root = tmp_path_factory.mktemp("sessions")
    engine, *_ = _run(root / "s-1" / "workspaces", [{"kind": "RESULT", "body": POSITIVE, "result_ir": _ir()}],
                      problem_class=VERIFIED)
    return root, f"pdlt://sessions/s-1/{engine.workspace.path.name}/{engine.workspace.turn_id}/"


def test_an_sdk_client_completes_the_handshake_and_reads_valid_tool_schemas(sessions, tmp_path):
    async def body(client):
        init = await client.initialize()
        tools = (await client.list_tools()).tools
        return init, tools

    init, tools = _session(sessions[0], tmp_path / "calls.jsonl", body)
    assert init.server_info.name == mcp_server.SERVER_NAME
    assert init.capabilities.tools is not None and init.capabilities.resources is not None
    assert "never instructions" in (init.instructions or "")
    assert [t.name for t in tools] == ["run_python", agent_tools.SUBMIT]
    for tool in tools:
        Draft202012Validator.check_schema(tool.input_schema)  # a valid JSON Schema, as published
        assert tool.input_schema.get("additionalProperties") is False
    assert tools[1].description.endswith(mcp_server.MCP_AFTER_ACCEPTANCE)


def test_tools_behave_as_documented_through_the_sdk(sessions, tmp_path):
    async def body(client):
        await client.initialize()
        ran = await client.call_tool("run_python", {"code": "print(6 * 7)"})
        extra = await client.call_tool("run_python", {"code": "print(1)", "timeout": 999})
        rejected = await client.call_tool(agent_tools.SUBMIT, {"outcome": _outcome("The answer is 42.")})
        accepted = await client.call_tool(agent_tools.SUBMIT, {"outcome": _outcome(GOOD)})
        try:
            await client.call_tool("read_attempt", {})
            unknown = None
        except McpError as exc:
            unknown = exc
        return ran, extra, rejected, accepted, unknown

    ran, extra, rejected, accepted, unknown = _session(sessions[0], tmp_path / "calls.jsonl", body,
                                                       "--witness-required")
    assert ran.is_error is False and "standard output:\n42" in _text(ran)
    assert extra.is_error is True and "do not match run_python's input schema" in _text(extra)
    assert rejected.is_error is True and rejected.structured_content["errors"][0]["code"] == "NO_PROGRAM"
    assert accepted.is_error is False and accepted.structured_content["result"] == mcp_server.MCP_ACCEPTED
    assert unknown is not None  # not offered: no previous attempt


def test_the_work_budget_holds_across_the_session(sessions, tmp_path):
    async def body(client):
        await client.initialize()
        results = [await client.call_tool("run_python", {"code": "print(1)"})
                   for _ in range(agent_tools.MAX_TOOL_CALLS + 1)]
        return results

    results = _session(sessions[0], tmp_path / "calls.jsonl", body)
    assert all(r.is_error is False for r in results[:-1])
    assert results[-1].is_error is True and "budget is spent" in _text(results[-1])


def test_resources_carry_their_provenance_and_unknown_uris_fail(sessions, tmp_path):
    root, base = sessions

    async def body(client):
        await client.initialize()
        listed = (await client.list_resources()).resources
        response = await client.read_resource(base + "response")
        try:
            await client.read_resource(base + "../../secret")
            missing = None
        except McpError as exc:
            missing = exc
        return listed, response, missing

    listed, response, missing = _session(root, tmp_path / "calls.jsonl", body)
    uris = [str(r.uri) for r in listed]
    assert uris == [base + "provenance", base + "response", base + "program-output"]
    assert all(r.description.startswith("CLOSED_SUCCESS, host_verified: ") for r in listed)
    assert [str(c.uri) for c in response.contents] == [base + "response", base + "provenance"]
    record = json.loads(response.contents[1].text)
    assert record["verification"]["level"] == "host_verified" and record["schema"] == "pdlt.provenance/1"
    assert missing is not None and missing.error.code == mcp_server.RESOURCE_NOT_FOUND


def test_every_sdk_request_is_in_the_call_log(sessions, tmp_path):
    log = tmp_path / "calls.jsonl"

    async def body(client):
        await client.initialize()
        await client.list_tools()
        await client.call_tool("run_python", {"code": "print(2 + 2)"})

    _session(sessions[0], log, body)
    records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    methods = [r.get("method") for r in records if r["event"] == "request"]
    assert methods[:2] == ["initialize", "notifications/initialized"] and "tools/list" in methods
    assert "tools/call" in methods
    tool = next(r for r in records if r["event"] == "tool")
    assert tool["tool"] == "run_python" and "standard output:\n4" in tool["output"]
    answered = {r["id"] for r in records if r["event"] == "response"}
    assert answered == {r["id"] for r in records if r["event"] == "request" and r["id"] is not None}


def test_the_server_refuses_to_start_without_confinement(tmp_path):
    proc = subprocess.run([sys.executable, "-m", "pdl_taskmaster.host.mcp_server", "--sandbox", "audit-only",
                           "--sessions", str(tmp_path), "--log", str(tmp_path / "calls.jsonl")],
                          cwd=ROOT, capture_output=True, text=True, timeout=60,
                          env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
    assert proc.returncode != 0 and "audit-only" in proc.stderr
