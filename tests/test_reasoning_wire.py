"""End to end: the runner's own command line, run against a stub /responses API,
sends the requested reasoning effort on every model call (2026-09-30: the gpt-oss
per-operation mapping silently pinned EXECUTE to "low" whatever --reasoning said)."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_REPLIES = {
    "BOOTSTRAP_ANALYSIS": {"kind": "ANALYSIS", "task_summary": "The user asks for the sum of two numbers.",
                           "approach_notes": "", "risk_notes": "", "task_entities": []},
    "DRAFT_PROMPT": {"kind": "PROMPT", "prompt_body": "COMPUTE the sum of 2 and 3", "approach_handoff": "NONE"},
    "DRAFT_PLAN": {"neutral_plan_body": "ADD 2 and 3\nRETURN the sum"},
    "EXECUTE": {"kind": "RESULT", "body": "5"},
}


def _stub_server(seen: list[tuple[str, object]]):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            text = json.dumps(body)
            match = re.search(r'\\"operation\\":\s*\\"([A-Z_]+)\\"|"operation":\s*"([A-Z_]+)"', text)
            operation = next((g for g in (match.groups() if match else ()) if g), "UNKNOWN")
            seen.append((operation, body.get("reasoning")))
            reply = _REPLIES.get(operation, {"kind": "RESULT", "body": "ok"})
            payload = {"status": "completed", "model": body.get("model"),
                       "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(reply)}]}],
                       "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}}
            data = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.mark.parametrize("effort, ops, expected", [
    ("low", [], {"BOOTSTRAP_ANALYSIS": "low", "DRAFT_PROMPT": "low", "DRAFT_PLAN": "low", "EXECUTE": "low"}),
    ("high", [], {"BOOTSTRAP_ANALYSIS": "high", "DRAFT_PROMPT": "high", "DRAFT_PLAN": "high", "EXECUTE": "high"}),
    ("low", ["EXECUTE=high"], {"BOOTSTRAP_ANALYSIS": "low", "DRAFT_PLAN": "low", "EXECUTE": "high"}),
    ("high", ["EXECUTE=low"], {"BOOTSTRAP_ANALYSIS": "high", "DRAFT_PLAN": "high", "EXECUTE": "low"}),
])
def test_runner_command_sends_the_requested_effort_per_operation(tmp_path, effort, ops, expected):
    import run_catalogue

    seen: list[tuple[str, object]] = []
    server = _stub_server(seen)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("What is 2 + 3?", encoding="utf-8")
    cmd = run_catalogue.build_harness_command(prompt, "stub-session", tmp_path / "t.txt", tmp_path / "s",
                                              "openai/gpt-oss-120b", effort, ops)
    cmd += ["--api-base-url", f"http://127.0.0.1:{server.server_address[1]}"]
    env = {k: v for k, v in os.environ.items() if not k.startswith(("SYS1", "OPENROUTER"))}
    env.update(OPENROUTER_API_KEY="stub", PYTHONPATH=str(ROOT / "src"))
    code, timed_out = run_catalogue.run_with_deadline(cmd, "/confirm\n" * 5, 120, tmp_path / "out.txt",
                                                      tmp_path / "err.txt", cwd=str(ROOT), env=env)
    server.shutdown()
    assert not timed_out, (tmp_path / "err.txt").read_text()
    sent = {op: (r or {}).get("effort") for op, r in seen}
    assert "EXECUTE" in sent, (seen, (tmp_path / "out.txt").read_text()[-2000:], (tmp_path / "err.txt").read_text()[-2000:])
    for operation, effort_sent in expected.items():
        assert sent.get(operation) == effort_sent, (operation, seen)
