"""Interruptions (Ctrl+C) at every point of a message's lifecycle.

Transport: before the request is sent, while it is sent, after it is sent but before
the API acknowledges it, after the acknowledgment, while the response arrives, and
after a retry. Engine: during each operation, between a state change and its
publication, and during a state write. REPL: what the user and the developer see.
"""
from __future__ import annotations

import http.server
import json
import sys
import threading
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import pytest

from pdl_taskmaster.fileio import replace_text
from pdl_taskmaster.providers import api_worker as module
from pdl_taskmaster.providers.api_worker import ApiWorker
from pdl_taskmaster.providers.call_trace import describe_interruption
from pdl_taskmaster.runtime.session_engine import SessionEngine

ROOT = Path(__file__).resolve().parents[1]
BODY = b'{"input": "x"}'


# ------------------------------------------------------------------ transport

class _Conn:
    pass


def _fake_urlopen(stop_at: str, chunks: tuple[bytes, ...] = (b'{"output": [], "status": "completed"}',)):
    """urlopen that emits http.client's audit events in order and raises KeyboardInterrupt
    at ``stop_at`` (connect, headers, body, ack, partial)."""

    class Response:
        status = 200

        def __init__(self):
            self.pending = list(chunks)
            self.delivered = False

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read1(self, n):
            if stop_at == "ack" or (stop_at == "partial" and self.delivered):
                raise KeyboardInterrupt  # partial: after the first chunk arrived
            if not self.pending:
                return b""
            self.delivered = True
            return self.pending.pop(0)

    def urlopen(req, timeout=None):
        conn = _Conn()
        if stop_at == "before":
            raise KeyboardInterrupt
        sys.audit("http.client.connect", conn, "example.invalid", 443)
        if stop_at == "connect":
            raise KeyboardInterrupt
        sys.audit("http.client.send", conn, b"POST / HTTP/1.1\r\nHost: example.invalid\r\n\r\n")
        if stop_at == "headers":
            raise KeyboardInterrupt
        sys.audit("http.client.send", conn, req.data)
        if stop_at == "body":
            raise KeyboardInterrupt  # sent; waiting for the status line
        return Response()

    return urlopen


def _call(monkeypatch, tmp_path, urlopen, operation="DRAFT_PROMPT"):
    monkeypatch.setattr(module.urllib.request, "urlopen", urlopen)
    worker = ApiWorker(model="m", repo_root=ROOT, timeout=60.0)
    worker.trace_path = tmp_path / "call-trace.jsonl"
    req = urllib.request.Request("https://example.invalid/v1/responses", data=BODY, method="POST")
    monkeypatch.setattr(worker, "_call", lambda request: worker._send_json_with_retries(req))
    with pytest.raises(KeyboardInterrupt):
        worker.call(SimpleNamespace(operation=operation))
    return worker


@pytest.mark.parametrize(
    "stop_at, reached, sent, acknowledged, started, words",
    [
        ("before", "prepared", False, False, False, "the request was not sent"),
        ("connect", "connecting", False, False, False, "the request was not sent"),
        ("headers", "connecting", False, False, False, "the request was not sent"),
        ("body", "request_sent", True, False, False, "sent but the API had not acknowledged it"),
        ("ack", "acknowledged", True, True, False, "the API had received the request; no response had arrived"),
        ("partial", "response_started", True, True, True, "partly received"),
    ],
)
def test_interruption_point_is_recorded(monkeypatch, tmp_path, stop_at, reached, sent, acknowledged, started, words):
    chunks = (b'{"out', b'put": []}') if stop_at == "partial" else (b"{}",)
    worker = _call(monkeypatch, tmp_path, _fake_urlopen(stop_at, chunks))
    (trace,) = worker.call_traces
    record = trace.to_dict()
    assert (record["final"], record["reached"], record["sent"], record["acknowledged"], record["response_started"]) \
        == ("interrupted", reached, sent, acknowledged, started)
    assert record["interrupted_by"] == "local" and record["attempts"][-1]["outcome"] == "interrupted"
    assert words in describe_interruption([trace])
    # The lifecycle is on disk although the call never returned.
    (line,) = (tmp_path / "call-trace.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(line)["final"] == "interrupted" and json.loads(line)["reached"] == reached


def test_partial_response_counts_the_bytes_received(monkeypatch, tmp_path):
    worker = _call(monkeypatch, tmp_path, _fake_urlopen("partial", (b"x" * 700, b"y" * 300)))
    assert worker.call_traces[-1].attempts[-1].response_bytes == 700
    assert "(700 bytes)" in describe_interruption(list(worker.call_traces))


def test_interruption_after_a_retry_is_reported_with_the_retry(monkeypatch, tmp_path):
    """First attempt: HTTP 503 (retried); second attempt interrupted while waiting."""
    calls = {"n": 0}
    interrupted = _fake_urlopen("body")

    def urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(req.full_url, 503, "busy", {}, None)
        return interrupted(req, timeout)

    monkeypatch.setattr(module, "_sleep_within", lambda delay, deadline: None)
    worker = _call(monkeypatch, tmp_path, urlopen)
    record = worker.call_traces[-1].to_dict()
    assert record["retries"] == 1
    first, second = record["attempts"]
    assert (first["outcome"], first["status"], first["retried"]) == ("http_error", 503, True)
    assert (second["outcome"], second["reached"]) == ("interrupted", "request_sent")
    assert "after 1 retry" in describe_interruption(list(worker.call_traces))


def test_remote_disconnect_is_not_a_local_interruption(monkeypatch, tmp_path):
    import http.client

    def urlopen(req, timeout=None):
        sys.audit("http.client.connect", _Conn(), "example.invalid", 443)
        sys.audit("http.client.send", _Conn(), req.data)
        raise http.client.RemoteDisconnected("closed")

    monkeypatch.setattr(module.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(module, "_sleep_within", lambda delay, deadline: None)
    worker = ApiWorker(model="m", repo_root=ROOT, timeout=60.0)
    req = urllib.request.Request("https://example.invalid/v1/responses", data=BODY, method="POST")
    monkeypatch.setattr(worker, "_call", lambda request: worker._send_json_with_retries(req))
    with pytest.raises(Exception):
        worker.call(SimpleNamespace(operation="EXECUTE"))
    record = worker.call_traces[-1].to_dict()
    assert record["final"] == "failed" and record["retries"] == 4
    assert {a["interrupted_by"] for a in record["attempts"]} == {"remote"}


def test_real_http_client_events_map_to_the_phases():
    """Against a real local server: connect, send, status line, body."""

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok": true}')

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        worker = ApiWorker(model="m", repo_root=ROOT, timeout=10.0)
        trace = worker.begin_call("DRAFT_PLAN")
        req = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/", data=BODY, method="POST")
        assert worker._send_json_with_retries(req) == {"ok": True}
        worker.end_call(trace)
    finally:
        server.shutdown()
    attempt = trace.attempts[-1]
    assert list(attempt.phases) == ["prepared", "connecting", "request_sent", "acknowledged", "response_started",
                                    "response_complete"]
    assert (attempt.status, attempt.outcome, attempt.response_bytes) == (200, "completed", len(b'{"ok": true}'))


# ------------------------------------------------------------------ engine

GOOD = {
    "BOOTSTRAP_ANALYSIS": {"kind": "ANALYSIS", "task_summary": "The user asks for a result.", "approach_notes": "",
                           "risk_notes": "", "task_entities": []},
    "DRAFT_PROMPT": {"kind": "PROMPT", "prompt_body": "COMPUTE the requested result", "approach_handoff": "NONE"},
    "DRAFT_PLAN": {"neutral_plan_body": "DERIVE the result\nRETURN it"},
    "EXECUTE": {"kind": "RESULT", "body": "The result is 1/3."},
}


class Worker:
    """System 2 stand-in that raises KeyboardInterrupt the first time ``interrupt_at`` is called."""

    def __init__(self, interrupt_at: str | None = None):
        self.interrupt_at = interrupt_at
        self.calls: list[str] = []

    def __call__(self, request):
        self.calls.append(request.operation)
        if request.operation == self.interrupt_at:
            self.interrupt_at = None
            raise KeyboardInterrupt
        return json.dumps(GOOD[request.operation])


def _events(engine, kind):
    return [e for e in engine.workspace.read_events() if e["kind"] == kind]


def _interrupted(engine, message):
    with pytest.raises(KeyboardInterrupt):
        engine.handle_user_message(message)
    return engine.record_interruption({"operation": "x"})


def test_interrupted_before_any_protocol_marks_the_turn_and_the_next_message_starts_afresh(tmp_path):
    engine = SessionEngine(ROOT, Worker("BOOTSTRAP_ANALYSIS"), workspace_root=tmp_path)
    info = _interrupted(engine, "$confirm-with-pseudocode a task")
    orphan = engine.workspace
    assert info["turn_status_before"] == "ACTIVE" and "INTERRUPTED" in info["action"]
    assert (info["last_operation"], info["last_operation_output_recorded"]) == ("BOOTSTRAP_ANALYSIS", False)
    assert orphan.read_turn_status("turn_001")["status"] == "INTERRUPTED"
    response = engine.handle_user_message("$confirm-with-pseudocode a task")
    assert engine.controller.state.stage.value == "PROMPT_REVIEW" and "Prompt Pseudocode" in response.text
    assert engine.workspace.path != orphan.path


@pytest.mark.parametrize("operation, stage_after, next_stage", [
    ("DRAFT_PLAN", "PLAN_REQUIRED", "PLAN_REVIEW"),
    ("EXECUTE", "EXECUTION_READY", "CLOSED_SUCCESS"),
])
def test_interrupted_inside_a_bound_protocol_keeps_its_state_and_resumes(tmp_path, operation, stage_after, next_stage):
    worker = Worker(operation)
    engine = SessionEngine(ROOT, worker, workspace_root=tmp_path)
    engine.handle_user_message("$confirm-with-pseudocode a task")
    if operation == "EXECUTE":
        engine.handle_user_message("/confirm")
    info = _interrupted(engine, "/confirm")
    assert info["stage"] == stage_after and info["persisted_stage"] == stage_after and info["state_persisted"]
    assert info["turn_status_before"] == "ACTIVE" and "kept" in info["action"]
    assert engine.workspace.read_turn_status("turn_001")["status"] == "ACTIVE"
    engine.handle_user_message("/confirm")  # the next input re-drives the interrupted step
    assert engine.controller.state.stage.value == next_stage
    assert worker.calls.count(operation) == 2
    (event,) = _events(engine, "TURN_INTERRUPTED")
    assert event["payload"]["last_operation"] == operation


def test_interrupted_follow_up_never_replaces_the_previous_turn(tmp_path):
    """Before the fix, the next message marked the never-run turn CLOSED_SUCCESS and the
    following turn lost the real previous deliverable."""
    worker = Worker()
    engine = SessionEngine(ROOT, worker, workspace_root=tmp_path)
    engine.handle_user_message("$confirm-with-pseudocode a task")
    engine.handle_user_message("/confirm")
    engine.handle_user_message("/confirm")
    assert engine.controller.state.stage.value == "CLOSED_SUCCESS"
    worker.interrupt_at = "BOOTSTRAP_ANALYSIS"
    info = _interrupted(engine, "$confirm-with-pseudocode now explain it")
    assert info["turn"] == "turn_002" and "INTERRUPTED" in info["action"]
    engine.handle_user_message("$confirm-with-pseudocode now explain it")
    ws = engine.workspace
    assert ws.turn_id == "turn_003"
    assert ws.read_turn_status("turn_002")["status"] == "INTERRUPTED"
    (chained,) = _events(engine, "TURN_CHAINED")
    assert chained["payload"]["previous_status"] == "CLOSED_SUCCESS" and chained["payload"]["previous_deliverable"]
    assert engine._previous_turn["turn_id"] == "turn_001"


def test_interrupted_between_the_state_change_and_its_publication(tmp_path, monkeypatch):
    """The prompt is committed to the controller but Ctrl+C lands before it is published."""
    engine = SessionEngine(ROOT, Worker(), workspace_root=tmp_path)
    original = engine._publish_prompt
    calls = {"n": 0}

    def publish():
        calls["n"] += 1
        if calls["n"] == 1:
            raise KeyboardInterrupt
        original()

    monkeypatch.setattr(engine, "_publish_prompt", publish)
    info = _interrupted(engine, "$confirm-with-pseudocode a task")
    assert info["stage"] == "PROMPT_REVIEW" and info["state_persisted"]
    response = engine.handle_user_message("/confirm")  # the review continues from the persisted state
    assert engine.controller.state.stage.value == "PLAN_REVIEW", response.text


def test_unpublished_review_is_repaired_by_the_next_input_even_without_the_handler(tmp_path, monkeypatch):
    """A crash (no interruption handler) between commit and publication: the next input
    republishes the review artifact from the controller state instead of failing forever."""
    engine = SessionEngine(ROOT, Worker(), workspace_root=tmp_path)
    original, calls = engine._publish_prompt, {"n": 0}

    def publish():
        calls["n"] += 1
        if calls["n"] == 1:
            raise KeyboardInterrupt
        original()

    monkeypatch.setattr(engine, "_publish_prompt", publish)
    with pytest.raises(KeyboardInterrupt):
        engine.handle_user_message("$confirm-with-pseudocode a task")
    engine.handle_user_message("/confirm")
    assert engine.controller.state.stage.value == "PLAN_REVIEW"
    assert [e["payload"]["kind"] for e in _events(engine, "ARTIFACT_REPUBLISHED")] == ["prompt"]


def test_a_state_write_interrupted_midway_leaves_the_previous_file(tmp_path, monkeypatch):
    target = tmp_path / "controller-state.json"
    target.write_text('{"stage": "PROMPT_REVIEW"}', encoding="utf-8")

    def replace(src, dst):
        raise KeyboardInterrupt

    monkeypatch.setattr("pdl_taskmaster.fileio.os.replace", replace)
    with pytest.raises(KeyboardInterrupt):
        replace_text(target, '{"stage": "PLAN_REVIEW"}')
    assert json.loads(target.read_text(encoding="utf-8")) == {"stage": "PROMPT_REVIEW"}
    assert [p.name for p in tmp_path.iterdir()] == ["controller-state.json"]  # no stray temporary file


# ------------------------------------------------------------------ REPL

def test_repl_reports_what_was_in_flight(monkeypatch, capsys, tmp_path):
    """The user sees where the interruption landed; dev mode adds the full record."""
    from test_repl_integration import _headless_runtime

    from pdl_taskmaster.providers.call_trace import CallTrace

    interrupted = CallTrace("DRAFT_PROMPT", final="interrupted")
    attempt = interrupted.new_attempt(BODY)
    attempt.mark("connecting")
    attempt.mark("request_sent")
    attempt.mark("acknowledged")
    attempt.status, attempt.outcome, attempt.interrupted_by = 200, "interrupted", "local"
    fake_worker = SimpleNamespace(call_traces=[], capture_tokens=False)

    def handle(line):
        fake_worker.call_traces.append(interrupted)
        raise KeyboardInterrupt

    repl, runtime = _headless_runtime(monkeypatch, tmp_path, handle, "PROMPT_REVIEW")
    runtime.host.record_interruption = lambda call: {
        "action": "turn marked INTERRUPTED", "stage": None, "persisted_stage": None, "state_persisted": True,
        "turn_status_before": "ACTIVE", "last_operation": "DRAFT_PROMPT", "last_operation_output_recorded": False,
    }
    runtime._refresh_pointer = lambda: None
    monkeypatch.setattr(repl, "build_recorded_fixture_from_vendored", lambda *a, **k: fake_worker)
    monkeypatch.setattr(sys, "argv", sys.argv + ["--dev"])
    with pytest.raises(KeyboardInterrupt):  # headless: an interrupt ends the run
        repl.main()
    out = capsys.readouterr().out
    assert "[operation interrupted by user] during DRAFT_PROMPT: the API had received the request" in out
    assert "turn marked INTERRUPTED" in out
    telemetry = json.loads(out.split("[dev:interrupt] ", 1)[1].splitlines()[0])
    assert telemetry["interrupted_by"] == "local" and telemetry["handled"] is True
    assert (telemetry["sent"], telemetry["acknowledged"], telemetry["response_started"]) == (True, True, False)
    assert "[dev:call] DRAFT_PROMPT call 1 (HTTP attempt 1), reached acknowledged, HTTP 200" in out
