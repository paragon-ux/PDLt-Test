"""The in-call agent tools (ADR-0029) served over MCP's stdio transport, for agents outside PDLt (ADR-0023 section 7,
TOOL_EXTRACTION_PLAN.md step 6). A thin adapter: the tool definitions, their handlers, budgets and the submission
check are runtime/agent_tools.py's, unchanged; this module only speaks JSON-RPC 2.0, one message per line.

    python -m pdl_taskmaster.host.mcp_server [--tier STANDARD] [--witness-required] [--sandbox auto] [--log PATH]

Served: initialize, ping, tools/list, tools/call. One server process is one session: initialize comes first and
once (only ping is answered before it), and the tool budgets and the sandbox last as long as the process. The
protocol revisions negotiated are SUPPORTED_PROTOCOL_VERSIONS; the stateless 2026-07-28 revision, which has no
initialize handshake, is not served. Every program runs in one confined session sandbox (ADR-0021) at
the tier's limits; the audit-only opt-out is refused. No tool returns a verdict; a submission is checked
structurally and accepted or returned with errors, and nothing verifies it afterwards here. Nothing here reads or
writes the user's project.

Also served, read-only (L117): resources/list and resources/read over the closed turns with a published result in
one sessions folder (``--sessions``, default the REPL's): each turn's response, as published, the output of the
programs the host ran for it, and its provenance (L121 flag E-1): the status, what the verification rests on and
what it does not establish. Every read of a turn's artifact returns its provenance with it. A resource is found by
listing; a client's URI is never joined into a path.

Every request is logged (L121 flag E-3): one JSON line before it runs and one after, plus each tool call and
submission as the tool host records it. A log that cannot be written stops the request; nothing runs unlogged.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TextIO

from pdl_taskmaster import __version__
from pdl_taskmaster.api import closed_sessions
from pdl_taskmaster.api.sandbox import SandboxNotConfined, create_sandbox
from pdl_taskmaster.runtime import agent_tools

# The protocol revisions initialize negotiates, newest first. A client asking for any other (2026-07-28 included:
# its stateless per-request envelope has no initialize handshake and is not served here) is offered the newest, as
# the lifecycle requires; a client that cannot use it disconnects.
SUPPORTED_PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
PROTOCOL_VERSION = SUPPORTED_PROTOCOL_VERSIONS[0]
STRUCTURED_RESULTS_SINCE = "2025-06-18"  # the revision that added outputSchema and structuredContent
BATCH_VERSIONS = ("2025-03-26",)  # the one revision with JSON-RPC batches: 2025-06-18 removed them
MAX_BATCH = 32
INVALID_REQUEST = -32600
SERVER_NAME = "pdlt-agent-tools"
URI_SCHEME = "pdlt://sessions/"
PAGE_SIZE = 100
RESOURCE_NOT_FOUND = -32002
INTERNAL_ERROR = -32603
LOG_TEXT_CHARS = 20000
# Outside the harness nothing verifies an accepted submission (L121 flag E-2).
MCP_AFTER_ACCEPTANCE = ("An accepted outcome has passed these structural checks only; this server does not verify "
                        "the deliverable afterwards.")
MCP_ACCEPTED = "accepted: the structural checks passed; nothing verifies the deliverable afterwards here"


class ClosedSessions:
    """The closed turns with a published result under one sessions folder, laid out as the REPL writes it:
    ``<root>/<session>/workspaces/<workspace>/turns/<turn>/``. Read-only."""

    def __init__(self, root: Path):
        self.root = root

    def resources(self) -> dict[str, tuple[Callable[[], str], dict[str, Any], str]]:
        """URI -> (reader, MCP resource, the turn's provenance URI) for every readable resource, in a stable order."""
        found: dict[str, tuple[Callable[[], str], dict[str, Any], str]] = {}
        for turn in closed_sessions.closed_turns(self.root):
            record = turn.provenance()
            if record is None:
                continue
            prefix = f"{URI_SCHEME}{turn.session}/{turn.workspace}/{turn.turn}/"
            level = record["verification"]["level"]
            text = json.dumps(record, ensure_ascii=False, indent=2)
            found[prefix + "provenance"] = (lambda text=text: text, {
                "uri": prefix + "provenance", "name": f"{turn.session} {turn.turn} provenance",
                "mimeType": "application/json",
                "description": f"{turn.status}, {level}: what the result rests on and what it does not establish"},
                prefix + "provenance")
            for part, file in turn.artifacts().items():
                _, mime, what = closed_sessions.ARTIFACTS[part]
                found[prefix + part] = (lambda file=file: file.read_text(encoding="utf-8"), {
                    "uri": prefix + part, "name": f"{turn.session} {turn.turn} {part}", "mimeType": mime,
                    "description": f"{turn.status}, {level}: {what}"}, prefix + "provenance")
        return found

    def list(self, cursor: str | None) -> dict[str, Any]:
        entries = [resource for _, resource, _ in self.resources().values()]
        start = int(cursor) if cursor and cursor.isdigit() else 0
        page: dict[str, Any] = {"resources": entries[start:start + PAGE_SIZE]}
        if start + PAGE_SIZE < len(entries):
            page["nextCursor"] = str(start + PAGE_SIZE)
        return page

    def read(self, uri: str) -> dict[str, Any] | None:
        """The resource, followed by its turn's provenance when the resource is an artifact (E-1)."""
        found = self.resources()
        entry = found.get(uri)
        if entry is None:
            return None
        reader, resource, provenance_uri = entry
        contents = [{"uri": uri, "mimeType": resource["mimeType"], "text": reader()}]
        if provenance_uri != uri:
            contents.append({"uri": provenance_uri, "mimeType": "application/json",
                             "text": found[provenance_uri][0]()})
        return {"contents": contents}


class CallLog:
    """Every request the server handles, as JSON lines (E-3). Opened when the server starts: a log that cannot be
    opened stops the server, and one that cannot be written stops the request."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._file = path.open("a", encoding="utf-8")

    def write(self, record: dict[str, Any]) -> None:
        self._file.write(json.dumps(_clip({"at": datetime.now(timezone.utc).isoformat(), **record}),
                                    ensure_ascii=False, default=str) + "\n")
        self._file.flush()

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> "CallLog":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()


def _clip(value: Any) -> Any:
    if isinstance(value, str):
        return value if len(value) <= LOG_TEXT_CHARS else value[:LOG_TEXT_CHARS] + f"... [{len(value)} chars]"
    if isinstance(value, dict):
        return {k: _clip(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clip(v) for v in value]
    return value


class AgentToolServer:
    """One MCP session over one tool host. ``host`` is an agent_tools.ToolHost; ``sessions``, when given, serves
    closed sessions' results as resources; ``log``, when given, records every request."""

    def __init__(self, host: agent_tools.ToolHost, sessions: ClosedSessions | None = None,
                 log: CallLog | None = None):
        self.host = host
        self.sessions = sessions
        self.log = log
        self.protocol_version: str | None = None  # negotiated by initialize
        if log is not None and host.on_record is None:
            host.on_record = lambda record: log.write({"event": "tool", **record})

    def tools(self) -> list[dict[str, Any]]:
        names = self.host.tool_names()
        tools = [dict(t) for t in agent_tools.TOOLS if t["name"] in names]  # MCP's shape, as defined
        for tool in tools:
            if tool["name"] == agent_tools.SUBMIT:
                tool["description"] = tool["description"].replace(agent_tools.VERIFIED_AFTER_ACCEPTANCE,
                                                                  MCP_AFTER_ACCEPTANCE)
                if self.structured:
                    tool["outputSchema"] = agent_tools.SUBMIT_RESULT_SCHEMA
        return tools

    @property
    def structured(self) -> bool:
        """Whether the negotiated revision has outputSchema and structuredContent."""
        return self.protocol_version is not None and self.protocol_version >= STRUCTURED_RESULTS_SINCE

    def call_tool(self, name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
        text = json.dumps(arguments or {})
        if name == agent_tools.SUBMIT:
            if len(self.host.submissions) >= agent_tools.MAX_SUBMISSIONS:
                return _content("error: the submission budget is spent", error=True)
            envelope, _accepted = self.host.submit(text)
            result = _content(json.dumps(envelope, ensure_ascii=False), error=not envelope["ok"])
            return {**result, "structuredContent": envelope} if self.structured else result
        if name in agent_tools.WORK_TOOLS and self.host.work_calls() >= agent_tools.MAX_TOOL_CALLS:
            return _content("error: the tool-call budget is spent", error=True)
        output = self.host.dispatch(name, text)
        return _content(output, error=output.startswith("error:"))

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """One JSON-RPC message, logged before it runs and after: the response, or None for a notification."""
        method, mid = message.get("method"), message.get("id")
        if self.log is not None:
            try:
                self.log.write({"event": "request", "id": mid, "method": method, "params": message.get("params")})
            except (OSError, ValueError) as exc:
                return None if "id" not in message else _error(
                    mid if _valid_id(mid) else None, INTERNAL_ERROR,
                    f"the call log cannot be written ({exc}); nothing ran")
        started = time.perf_counter()
        response = self._handle(message)
        if self.log is not None and response is not None:
            result = (response or {}).get("result")
            self.log.write({"event": "response", "id": mid, "method": method,
                            "ms": round((time.perf_counter() - started) * 1000, 1),
                            "error": (response or {}).get("error"),
                            "is_error": result.get("isError") if isinstance(result, dict) else None})
        return response

    def _handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method, params = message.get("method"), message.get("params") or {}
        if "id" not in message:
            return None  # notifications (notifications/initialized, cancellations) need no answer
        mid = message["id"]
        if not _valid_id(mid):
            return _error(None, INVALID_REQUEST, "a request id must be a string or an integer")
        if not isinstance(params, dict):
            return _error(mid, -32602, "params must be an object")
        if method == "initialize":
            if self.protocol_version is not None:
                return _error(mid, INVALID_REQUEST, "already initialized: a new session needs a new server process")
            requested = params.get("protocolVersion")
            self.protocol_version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else PROTOCOL_VERSION
            capabilities: dict[str, Any] = {"tools": {"listChanged": False}}
            if self.sessions is not None:
                capabilities["resources"] = {"listChanged": False, "subscribe": False}
            result: Any = {"protocolVersion": self.protocol_version, "capabilities": capabilities,
                           "serverInfo": {"name": SERVER_NAME, "version": __version__},
                           "instructions": self.host.capability_note()}
        elif method == "ping":
            result = {}
        elif method not in self._methods():
            return _error(mid, -32601, f"method not found: {method!r}")
        elif self.protocol_version is None:
            # Nothing that can run a program is served before the version is negotiated.
            return _error(mid, INVALID_REQUEST, "not initialized: send initialize first")
        elif method == "tools/list":
            result = {"tools": self.tools()}
        elif method == "tools/call":
            name = params.get("name")
            if name not in self.host.tool_names():
                return _error(mid, -32602, f"unknown tool: {name!r}")
            result = self.call_tool(name, params.get("arguments"))
        elif method == "resources/list":
            result = self.sessions.list(params.get("cursor"))
        else:  # resources/read
            result = self.sessions.read(str(params.get("uri", "")))
            if result is None:
                return _error(mid, RESOURCE_NOT_FOUND, f"resource not found: {params.get('uri')!r}")
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    def _methods(self) -> set[str]:
        """The methods served after initialize, besides ping."""
        return {"tools/list", "tools/call"} | ({"resources/list", "resources/read"} if self.sessions else set())

    def handle_batch(self, messages: list[Any]) -> list[dict[str, Any]] | dict[str, Any] | None:
        """A JSON-RPC batch, served only under 2025-03-26, the one revision with batches: the responses to its
        requests, in order, or None when it holds only notifications. Each element is handled and logged as if sent
        alone, under the session's budgets. The whole batch is refused with one error, and nothing in it runs, when
        it comes before initialize or under another revision, is empty or larger than MAX_BATCH, or holds
        initialize."""
        if self.protocol_version is None:
            problem = "not initialized: send initialize first, on its own"
        elif self.protocol_version not in BATCH_VERSIONS:
            problem = f"protocol version {self.protocol_version} has no batches"
        elif not messages:
            problem = "an empty batch"
        elif len(messages) > MAX_BATCH:
            problem = f"a batch of {len(messages)} messages; at most {MAX_BATCH}"
        elif any(isinstance(m, dict) and m.get("method") == "initialize" for m in messages):
            problem = "initialize cannot be part of a batch"
        else:
            responses = [self.handle(m) if isinstance(m, dict) else _error(None, INVALID_REQUEST, "invalid request")
                         for m in messages]
            return [r for r in responses if r is not None] or None
        if self.log is not None:
            try:
                self.log.write({"event": "batch", "size": len(messages), "error": problem})
            except (OSError, ValueError):
                pass  # nothing in the batch runs either way
        return _error(None, INVALID_REQUEST, problem)


def _valid_id(mid: Any) -> bool:
    """A request id: a string or an integer, never null (MCP)."""
    return isinstance(mid, (str, int)) and not isinstance(mid, bool)


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
            if isinstance(message, dict):
                response = server.handle(message)
            elif isinstance(message, list):
                response = server.handle_batch(message)
            else:
                response = _error(None, INVALID_REQUEST, "invalid request")
        if response is not None:
            stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            stdout.flush()


def build_host(tier: str = "STANDARD", witness_required: bool = False, sandbox_mode: str = "auto",
               repo_root: Path | None = None) -> agent_tools.ToolHost:
    """The tool host an outside agent gets: the session sandbox at ``tier``'s limits and the host's own
    submission check; no previous attempt, so no read_attempt. Programs from outside run only under OS-native
    confinement: the audit-only opt-out is refused (L121 flag E-4)."""
    from pdl_taskmaster.api.session import default_repo_root
    from pdl_taskmaster.runtime.operation_bridge import OperationBridge
    from pdl_taskmaster.runtime.session_engine import _parse_sandbox_witness, _python_blocks
    from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS

    budget = EXECUTION_BUDGETS[tier]
    try:
        sandbox = create_sandbox(sandbox_mode, label="mcp", require_confined=True)
    except SandboxNotConfined:
        raise SystemExit("the MCP server runs programs only under OS-native confinement; "
                         f"--sandbox {sandbox_mode} is refused") from None
    root = repo_root or default_repo_root()
    validate = agent_tools.make_validator(OperationBridge(root), sandbox, budget, witness_required, _python_blocks,
                                          _parse_sandbox_witness)
    return agent_tools.ToolHost(sandbox, budget.step_limit, budget.timeout_seconds, budget.memory_limit_bytes,
                                [], "", validate, accepted_note=MCP_ACCEPTED)


def main(argv: list[str] | None = None) -> int:
    from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS

    parser = argparse.ArgumentParser(prog="python -m pdl_taskmaster.host.mcp_server",
                                     description="Serve PDLt's in-call agent tools over MCP (stdio).")
    parser.add_argument("--tier", choices=sorted(EXECUTION_BUDGETS), default="STANDARD",
                        help="the execution budget every program runs under (default STANDARD)")
    parser.add_argument("--witness-required", action="store_true",
                        help="a submission must contain a program that prints a WITNESS line")
    parser.add_argument("--sandbox", default="auto", choices=["auto", "native", "container"],
                        help="sandbox backend, as for the harness; the audit-only opt-out is not offered "
                             "(default auto)")
    parser.add_argument("--sessions", type=Path, default=None,
                        help="the sessions folder whose closed results are served read-only (default: the REPL's)")
    parser.add_argument("--log", type=Path, default=None,
                        help="the JSON-lines call log (default: a new file in mcp-server/ beside the sessions folder)")
    args = parser.parse_args(argv)
    if args.sessions is None:
        from pdl_taskmaster.host.repl import _default_session_base

        args.sessions = _default_session_base()
    if args.log is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        args.log = args.sessions.parent / "mcp-server" / f"calls-{stamp}-{os.getpid()}.jsonl"
    try:
        log = CallLog(args.log)
    except OSError as exc:
        raise SystemExit(f"the call log {args.log} cannot be opened ({exc}); the server does not run unlogged")
    # utf-8-sig on stdin drops a leading byte-order mark (Windows PowerShell adds one to piped text), which
    # would otherwise make the first request a parse error.
    for stream, encoding in ((sys.stdin, "utf-8-sig"), (sys.stdout, "utf-8")):
        try:
            stream.reconfigure(encoding=encoding)
        except Exception:
            pass
    with log:
        host = build_host(args.tier, args.witness_required, args.sandbox)
        try:
            serve(AgentToolServer(host, ClosedSessions(args.sessions), log), sys.stdin, sys.stdout)
        finally:
            host.sandbox.close()  # the session sandbox's root and backend state
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
