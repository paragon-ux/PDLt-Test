"""The in-call agent tools (ADR-0029) served over MCP's stdio transport, for agents outside PDLt (ADR-0023 section 7,
TOOL_EXTRACTION_PLAN.md step 6). A thin adapter: the tool definitions, their handlers, budgets and the submission
check are runtime/agent_tools.py's, unchanged; this module only speaks JSON-RPC 2.0, one message per line.

    python -m pdl_taskmaster.host.mcp_server [--tier STANDARD] [--witness-required] [--sandbox auto]

Served: initialize, ping, tools/list, tools/call. Every program runs in one confined session sandbox (ADR-0021) at
the tier's limits; no tool returns a verdict; a submission is checked structurally and accepted or returned with
errors, as inside the harness. Nothing here reads or writes the user's project.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TextIO

from pdl_taskmaster import __version__
from pdl_taskmaster.runtime import agent_tools

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "pdlt-agent-tools"


class AgentToolServer:
    """One MCP session over one tool host. ``host`` is an agent_tools.ToolHost."""

    def __init__(self, host: agent_tools.ToolHost):
        self.host = host

    def tools(self) -> list[dict[str, Any]]:
        names = self.host.tool_names()
        return [dict(t) for t in agent_tools.TOOLS if t["name"] in names]  # MCP's shape, as defined

    def call_tool(self, name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
        text = json.dumps(arguments or {})
        if name == agent_tools.SUBMIT:
            if len(self.host.submissions) >= agent_tools.MAX_SUBMISSIONS:
                return _content("error: the submission budget is spent", error=True)
            envelope, _accepted = self.host.submit(text)
            return {**_content(json.dumps(envelope, ensure_ascii=False), error=not envelope["ok"]),
                    "structuredContent": envelope}
        if name in agent_tools.WORK_TOOLS and self.host.work_calls() >= agent_tools.MAX_TOOL_CALLS:
            return _content("error: the tool-call budget is spent", error=True)
        output = self.host.dispatch(name, text)
        return _content(output, error=output.startswith("error:"))

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """One JSON-RPC message: the response, or None for a notification."""
        method, mid, params = message.get("method"), message.get("id"), message.get("params") or {}
        if mid is None:
            return None  # notifications (notifications/initialized, cancellations) need no answer
        if method == "initialize":
            result: Any = {"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {"listChanged": False}},
                           "serverInfo": {"name": SERVER_NAME, "version": __version__},
                           "instructions": self.host.capability_note()}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": self.tools()}
        elif method == "tools/call":
            name = params.get("name")
            if name not in self.host.tool_names():
                return _error(mid, -32602, f"unknown tool: {name!r}")
            result = self.call_tool(name, params.get("arguments"))
        else:
            return _error(mid, -32601, f"method not found: {method!r}")
        return {"jsonrpc": "2.0", "id": mid, "result": result}


def _content(text: str, *, error: bool) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "isError": error}


def _error(mid: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}}


def serve(server: AgentToolServer, stdin: TextIO, stdout: TextIO) -> None:
    for line in stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except ValueError:
            response: dict[str, Any] | None = _error(None, -32700, "parse error")
        else:
            response = server.handle(message) if isinstance(message, dict) else _error(None, -32600, "invalid request")
        if response is not None:
            stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            stdout.flush()


def build_host(tier: str = "STANDARD", witness_required: bool = False, sandbox_mode: str = "auto",
               repo_root: Path | None = None) -> agent_tools.ToolHost:
    """The tool host an outside agent gets: the session sandbox at ``tier``'s limits and the host's own
    submission check; no previous attempt, so no read_attempt."""
    import pdl_taskmaster
    from pdl_taskmaster.runtime.operation_bridge import OperationBridge
    from pdl_taskmaster.runtime.session_engine import _parse_sandbox_witness, _python_blocks
    from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS, ExecutionSandbox

    budget = EXECUTION_BUDGETS[tier]
    sandbox = ExecutionSandbox(mode=sandbox_mode, label="mcp")
    root = repo_root or Path(pdl_taskmaster.__file__).resolve().parents[2]
    validate = agent_tools.make_validator(OperationBridge(root), sandbox, budget, witness_required, _python_blocks,
                                          _parse_sandbox_witness)
    return agent_tools.ToolHost(sandbox, budget.step_limit, budget.timeout_seconds, budget.memory_limit_bytes,
                                [], "", validate)


def main(argv: list[str] | None = None) -> int:
    from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS

    parser = argparse.ArgumentParser(prog="python -m pdl_taskmaster.host.mcp_server",
                                     description="Serve PDLt's in-call agent tools over MCP (stdio).")
    parser.add_argument("--tier", choices=sorted(EXECUTION_BUDGETS), default="STANDARD",
                        help="the execution budget every program runs under (default STANDARD)")
    parser.add_argument("--witness-required", action="store_true",
                        help="a submission must contain a program that prints a WITNESS line")
    parser.add_argument("--sandbox", default="auto", help="sandbox mode, as for the harness (default auto)")
    args = parser.parse_args(argv)
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    serve(AgentToolServer(build_host(args.tier, args.witness_required, args.sandbox)), sys.stdin, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
