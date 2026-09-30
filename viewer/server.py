"""PDLt local viewer server (evaluation plane).

Read-only, localhost-only HTTP server that shows:
  * the newest live/catalogue session (stage, prompt, plan, code, witness, transcript),
  * every catalogue run under ``catalogue-runs/`` with scoreboard and per-prompt results,
  * the 105-prompt catalogue.

It imports nothing from the harness package: it only reads files the harness and
runner wrote. Usage: ``python -m viewer [--port 8090] [--no-open] [--root DIR]``.
"""
from __future__ import annotations

import argparse
import http.server
import json
import os
import re
import socketserver
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

DEFAULT_ROOT = Path(os.environ.get("PDLT_VIEWER_ROOT", Path(__file__).resolve().parent.parent))
INDEX_HTML = Path(__file__).with_name("index.html")
LOG_TAIL_LINES = 200


# --------------------------------------------------------------------------- helpers

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(_read(path))
    except Exception:
        return None


def _newest(paths: list[Path]) -> Path | None:
    return max(paths, key=lambda p: p.stat().st_mtime) if paths else None


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


# --------------------------------------------------------------------------- sessions

def session_candidates(root: Path) -> list[Path]:
    """Directories that may hold protocol workspaces: live sessions and runner sessions."""
    found: list[Path] = []
    live = root / "runs" / "live-sessions"
    if live.is_dir():
        found += [p for p in live.iterdir() if p.is_dir()]
    runs = root / "catalogue-runs"
    if runs.is_dir():
        found += [p for p in runs.glob("run-*/results/*") if p.is_dir()]
    return found


def _activity(path: Path) -> float:
    files = [p for p in path.rglob("*") if p.is_file()]
    return max((p.stat().st_mtime for p in files), default=path.stat().st_mtime)


def latest_session_dir(root: Path) -> Path | None:
    candidates = session_candidates(root)
    return max(candidates, key=_activity) if candidates else None


_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.S)
_PY = re.compile(r"```(?:python|py)\s*\n(.*?)```", re.S)


def _witness_from(deliverable: str) -> Any:
    for block in reversed(_FENCE.findall(deliverable)):
        try:
            obj = json.loads(block)
        except Exception:
            continue
        if isinstance(obj, dict) and obj.get("witness"):
            return obj["witness"]
    return None


def read_session(session_dir: Path | None) -> dict[str, Any]:
    empty = {
        "session_id": "NONE", "stage": "IDLE", "active": False, "prompt": None, "plan": None,
        "code_snippet": None, "witness": None, "deliverable": None, "logs": [], "result": None,
    }
    if session_dir is None or not session_dir.is_dir():
        return empty

    state_file = _newest(list(session_dir.rglob("controller-state.json")))
    state = (_read_json(state_file) if state_file else None) or {}
    prompt = (state.get("current_prompt") or {}).get("body")
    plan = (state.get("current_plan") or {}).get("body")

    current = _newest([
        p for p in session_dir.rglob("current.md") if p.parent.match("*/stages/50_execution/output")
    ])
    deliverable = _read(current) if current else None
    code = None
    if deliverable:
        m = _PY.search(deliverable)
        code = m.group(1).strip() if m else None

    logs: list[str] = []
    transcript = session_dir / "transcript.txt"
    if transcript.is_file():
        logs = _read(transcript).splitlines()
    else:
        progress = _newest(list(session_dir.rglob("worker-progress.log")) + list(session_dir.rglob("transcript.log")))
        if progress:
            logs = _read(progress).splitlines()

    return {
        "session_id": session_dir.name,
        "stage": state.get("stage") or ("CLOSED_SUCCESS" if deliverable else "IDLE"),
        "active": True,
        "prompt": prompt,
        "plan": plan,
        "code_snippet": code,
        "witness": _witness_from(deliverable) if deliverable else None,
        "deliverable": deliverable,
        "logs": logs[-LOG_TAIL_LINES:],
        "result": _read_json(session_dir / "result.json"),
    }


# --------------------------------------------------------------------------- runs & catalogue

def list_runs(root: Path) -> list[dict[str, Any]]:
    runs_dir = root / "catalogue-runs"
    out: list[dict[str, Any]] = []
    if not runs_dir.is_dir():
        return out
    for run in sorted((p for p in runs_dir.glob("run-*") if p.is_dir()), reverse=True):
        board = _read_json(run / "SCOREBOARD.json") or {}
        meta = _read_json(run / "RUN_META.json") or {}
        results = sorted((run / "results").glob("*/result.json")) if (run / "results").is_dir() else []
        out.append({
            "id": run.name,
            "model": board.get("model") or meta.get("model"),
            "reasoning_effort": board.get("reasoning_effort") or meta.get("reasoning_effort"),
            "total": board.get("total_prompts", len(results)),
            "passed": board.get("passed"),
            "pass_rate_pct": board.get("pass_rate_pct"),
            "ground_truth": board.get("ground_truth"),
            "false_positives": len(board.get("false_positives") or []),
            "complete": bool(board),
        })
    return out


def read_run(root: Path, run_id: str) -> dict[str, Any] | None:
    run = root / "catalogue-runs" / run_id
    if not run.is_dir() or not _inside(root / "catalogue-runs", run):
        return None
    items = []
    for f in sorted((run / "results").glob("*/result.json")):
        r = _read_json(f) or {}
        grade = r.get("ground_truth_grade") or {}
        items.append({
            "id": r.get("id"), "category": r.get("category"), "verdict": r.get("verdict"),
            "expected_stage": r.get("expected_stage"), "elapsed_seconds": r.get("elapsed_seconds"),
            "grade": grade.get("grade"), "grade_reason": grade.get("reason"),
            "path": f.parent.relative_to(root).as_posix(),
        })
    return {"id": run_id, "scoreboard": _read_json(run / "SCOREBOARD.json"), "results": items}


def read_catalogue(root: Path) -> list[dict[str, Any]]:
    manifest = root / "prompts" / "CATALOGUE_MANIFEST.jsonl"
    if not manifest.is_file():
        return []
    items = []
    for line in _read(manifest).splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        items.append({
            "id": e["id"], "category": e["category"], "name": Path(e["file"]).stem,
            "difficulty": e.get("difficulty"), "ground_truth_status": e.get("ground_truth_status"),
        })
    return items


def read_prompt(root: Path, prompt_id: str) -> str | None:
    manifest = root / "prompts" / "CATALOGUE_MANIFEST.jsonl"
    if not manifest.is_file():
        return None
    for line in _read(manifest).splitlines():
        if line.strip() and json.loads(line)["id"] == prompt_id:
            return _read(root / "prompts" / json.loads(line)["file"])
    return None


# --------------------------------------------------------------------------- HTTP

class _Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, request, client_address):
        if sys.exc_info()[0] in (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            return
        super().handle_error(request, client_address)


def make_handler(root: Path):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):  # keep the console quiet
            pass

        def _send(self, status: int, body: bytes, ctype: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, payload: Any, status: int = 200) -> None:
            self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json")

        def do_GET(self):
            try:
                url = urlparse(self.path)
                q = {k: v[0] for k, v in parse_qs(url.query).items()}
                if url.path in {"/", "/index.html"}:
                    return self._send(200, INDEX_HTML.read_bytes(), "text/html; charset=utf-8")
                if url.path == "/api/status":
                    target = None
                    if q.get("path"):
                        target = (root / q["path"]).resolve()
                        allowed = [root / "catalogue-runs", root / "runs"]
                        if not any(_inside(a, target) for a in allowed):
                            return self._json({"error": "path outside viewer roots"}, 400)
                    else:
                        target = latest_session_dir(root)
                    return self._json(read_session(target))
                if url.path == "/api/runs":
                    return self._json(list_runs(root))
                if url.path == "/api/run":
                    data = read_run(root, q.get("id", ""))
                    return self._json(data if data else {"error": "unknown run"}, 200 if data else 404)
                if url.path == "/api/catalogue":
                    return self._json(read_catalogue(root))
                if url.path == "/api/prompt":
                    text = read_prompt(root, q.get("id", ""))
                    return self._json({"id": q.get("id"), "text": text}, 200 if text is not None else 404)
                self._send(404, b"not found", "text/plain")
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass

    return Handler


def start_server(root: Path = DEFAULT_ROOT, port: int = 8090) -> tuple[threading.Thread, _Server, int]:
    """Bind 127.0.0.1 only. ``port=0`` picks a free port; otherwise try port..port+9."""
    handler = make_handler(Path(root))
    candidates = [0] if port == 0 else list(range(port, port + 10))
    server = None
    for p in candidates:
        try:
            server = _Server(("127.0.0.1", p), handler)
            break
        except OSError:
            continue
    if server is None:
        raise OSError("could not bind viewer to any port in range")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread, server, server.server_address[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m viewer", description="PDLt local viewer (localhost only).")
    parser.add_argument("--port", "-p", type=int, default=8090, help="starting port (default 8090)")
    parser.add_argument("--no-open", action="store_true", help="do not open a browser")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="repository root holding catalogue-runs/ and prompts/")
    args = parser.parse_args(argv)
    try:
        _, server, port = start_server(args.root, args.port)
    except OSError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    url = f"http://127.0.0.1:{port}"
    print(f"PDLt viewer running on {url}  (root: {Path(args.root).resolve()})\nPress Ctrl+C to stop.", flush=True)
    if not args.no_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping viewer...", flush=True)
        server.shutdown()
        server.server_close()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
