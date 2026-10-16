"""L117 (narrowed by the user, 2026-10-15): a closed session's response and the output of the programs the host ran
for it are readable by outside clients through the existing MCP server, as read-only resources. No tool reaches
outside the sandbox. Offline; no model call."""
from __future__ import annotations

import json
from pathlib import Path

from pdl_taskmaster.host import mcp_server

from test_execution_phase import _ir, _run

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ("import json\nvalues = [3, 8, 5]\n"
           "print('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'largest': max(values)}}))")


def _server(sessions: Path | None) -> mcp_server.AgentToolServer:
    host = mcp_server.build_host("STANDARD", False, repo_root=ROOT)
    return mcp_server.AgentToolServer(host, mcp_server.ClosedSessions(sessions) if sessions else None)


def _rpc(server, method, params=None):
    return server.handle({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})


def _turn(root: Path, session: str, status: str, response: str | None, programs: list | None = None) -> None:
    turn = root / session / "workspaces" / "W-1" / "turns" / "turn_001"
    output = turn / "stages" / "50_execution" / "output"
    output.mkdir(parents=True)
    (turn / "turn.json").write_text(json.dumps({"turn_id": "turn_001", "status": status}), encoding="utf-8")
    if response is not None:
        (output / "current.md").write_text(response, encoding="utf-8")
    if programs is not None:
        (output / "program-output.json").write_text(json.dumps({"runs": programs}), encoding="utf-8")


def test_a_closed_result_keeps_the_output_of_the_programs_the_host_ran(tmp_path):
    engine, _, _, _ = _run(tmp_path, [{"kind": "RESULT", "body": PROGRAM, "result_ir": _ir()}],
                           problem_class="VERIFIED_EXECUTION")
    output = engine.workspace.path / "turns" / engine.workspace.turn_id / "stages" / "50_execution" / "output"
    runs = json.loads((output / "program-output.json").read_text(encoding="utf-8"))["runs"]
    assert [(r["block"], r["exit_code"]) for r in runs] == [(1, 0)]
    assert runs[0]["stdout"].strip() == 'WITNESS: {"polarity": "positive", "data": {"largest": 8}}'


def test_a_closed_result_is_listed_and_read_through_the_mcp_server(tmp_path):
    sessions = tmp_path / "sessions"
    engine, response, _, _ = _run(sessions / "session-1" / "workspaces",  # the REPL's layout (repl.py)
                                  [{"kind": "RESULT", "body": PROGRAM, "result_ir": _ir()}],
                                  problem_class="VERIFIED_EXECUTION")
    server = _server(sessions)
    initialized = _rpc(server, "initialize", {"protocolVersion": mcp_server.PROTOCOL_VERSION, "capabilities": {},
                                              "clientInfo": {"name": "t", "version": "0"}})["result"]
    assert initialized["capabilities"]["resources"] == {"listChanged": False, "subscribe": False}
    listed = _rpc(server, "resources/list")["result"]["resources"]
    turn = engine.workspace.turn_id
    workspace = engine.workspace.path.name
    base = f"pdlt://sessions/session-1/{workspace}/{turn}/"
    assert [r["uri"] for r in listed] == [base + "provenance", base + "response", base + "program-output"]
    assert all(r["description"].startswith("CLOSED_SUCCESS, host_verified: ") for r in listed)  # L121 E-1
    read = _rpc(server, "resources/read", {"uri": base + "response"})["result"]["contents"][0]
    assert read["mimeType"] == "text/markdown" and read["text"].rstrip() == response.text.rstrip()
    programs = json.loads(_rpc(server, "resources/read", {"uri": base + "program-output"})["result"]["contents"][0]["text"])
    assert '"largest": 8' in programs["runs"][0]["stdout"]


def test_only_closed_turns_with_a_result_are_served(tmp_path):
    _turn(tmp_path, "s-success", "CLOSED_SUCCESS", "Forty-two.", [{"block": 1, "exit_code": 0, "stdout": "42\n"}])
    _turn(tmp_path, "s-unverified", "CLOSED_UNVERIFIED", "No result exists.")
    _turn(tmp_path, "s-cancelled", "CLOSED_CANCELLED", None)
    _turn(tmp_path, "s-open", "EXECUTING", "draft")
    listed = {r["uri"]: r for r in _rpc(_server(tmp_path), "resources/list")["result"]["resources"]}
    assert sorted(listed) == ["pdlt://sessions/s-success/W-1/turn_001/program-output",
                              "pdlt://sessions/s-success/W-1/turn_001/provenance",
                              "pdlt://sessions/s-success/W-1/turn_001/response",
                              "pdlt://sessions/s-unverified/W-1/turn_001/provenance",
                              "pdlt://sessions/s-unverified/W-1/turn_001/response"]
    assert listed["pdlt://sessions/s-unverified/W-1/turn_001/response"]["description"].startswith("CLOSED_UNVERIFIED")


def test_a_uri_is_found_by_listing_never_by_joining_a_path(tmp_path):
    _turn(tmp_path, "s-open", "EXECUTING", "draft")
    (tmp_path / "secret.txt").write_text("not served", encoding="utf-8")
    server = _server(tmp_path)
    for uri in ("pdlt://sessions/s-open/W-1/turn_001/response", "pdlt://sessions/../secret.txt",
                "pdlt://sessions/s-open/W-1/turn_001/../../../../../secret.txt", "file:///etc/passwd", ""):
        assert _rpc(server, "resources/read", {"uri": uri})["error"]["code"] == mcp_server.RESOURCE_NOT_FOUND


def test_resources_are_listed_in_pages(tmp_path, monkeypatch):
    _turn(tmp_path, "s-a", "CLOSED_SUCCESS", "a")
    _turn(tmp_path, "s-b", "CLOSED_SUCCESS", "b")
    monkeypatch.setattr(mcp_server, "PAGE_SIZE", 1)
    server = _server(tmp_path)
    first = _rpc(server, "resources/list")["result"]
    second = _rpc(server, "resources/list", {"cursor": first["nextCursor"]})["result"]
    third = _rpc(server, "resources/list", {"cursor": second["nextCursor"]})["result"]
    fourth = _rpc(server, "resources/list", {"cursor": third["nextCursor"]})["result"]
    assert [r["name"] for r in first["resources"] + second["resources"] + third["resources"]
            + fourth["resources"]] == ["s-a turn_001 provenance", "s-a turn_001 response",
                                       "s-b turn_001 provenance", "s-b turn_001 response"]
    second = fourth
    assert "nextCursor" not in second


def test_without_a_sessions_folder_no_resources_are_served(tmp_path):
    server = _server(None)
    assert "resources" not in _rpc(server, "initialize")["result"]["capabilities"]
    assert _rpc(server, "resources/list")["error"]["code"] == -32601
