"""Viewer (evaluation plane): endpoints, session discovery on the runner layout, path safety."""
from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from viewer.server import latest_session_dir, read_catalogue, read_run, read_session, start_server

DELIVERABLE = """Solution below.

```python
print("WITNESS: {\\"answer\\": 42}")
```

```json
{"files": [], "reconciliation": [], "witness": {"polarity": "positive", "data": {"answer": 42}}}
```
"""


def _make_root(tmp_path: Path) -> Path:
    root = tmp_path
    prompts = root / "prompts" / "01_x"
    prompts.mkdir(parents=True)
    (prompts / "demo_prompt.txt").write_text("Solve the demo.", encoding="utf-8")
    entry = {"id": "01-01", "category": "x", "file": "01_x/demo_prompt.txt", "difficulty": "easy", "ground_truth_status": "verified"}
    (root / "prompts" / "CATALOGUE_MANIFEST.jsonl").write_text(json.dumps(entry) + "\n", encoding="utf-8")

    run = root / "catalogue-runs" / "run-20260101-000000"
    result_dir = run / "results" / "01-01_demo_prompt"
    out = result_dir / "session" / "W-abc" / "turns" / "turn_001" / "stages" / "50_execution" / "output"
    state = result_dir / "session" / "W-abc" / "turns" / "turn_001" / "state"
    out.mkdir(parents=True)
    state.mkdir(parents=True)
    (out / "current.md").write_text(DELIVERABLE, encoding="utf-8")
    (state / "controller-state.json").write_text(
        json.dumps({"stage": "CLOSED_SUCCESS", "current_prompt": {"body": "SOLVE demo"}, "current_plan": {"body": "COMPUTE answer"}}),
        encoding="utf-8",
    )
    (result_dir / "transcript.txt").write_text("[dev:telemetry] controller stage: PROMPT_REVIEW\n> \n", encoding="utf-8")
    (result_dir / "result.json").write_text(
        json.dumps({
            "id": "01-01", "category": "x", "verdict": "CLOSED_SUCCESS", "expected_stage": "CLOSED_SUCCESS",
            "exit_code": 0, "elapsed_seconds": 1.5, "ground_truth_grade": {"grade": "PASS", "reason": "ok"},
        }),
        encoding="utf-8",
    )
    (run / "SCOREBOARD.json").write_text(
        json.dumps({"model": "m", "reasoning_effort": "low", "total_prompts": 1, "passed": 1, "pass_rate_pct": 100.0,
                    "ground_truth": {"PASS": 1, "FAIL": 0, "MANUAL": 0}, "false_positives": []}),
        encoding="utf-8",
    )
    return root


def _get(base: str, path: str):
    with urllib.request.urlopen(base + path) as resp:
        return resp.status, resp.read()


def test_read_session_on_runner_layout(tmp_path):
    root = _make_root(tmp_path)
    target = latest_session_dir(root)
    assert target is not None and target.name == "01-01_demo_prompt"
    s = read_session(target)
    assert s["stage"] == "CLOSED_SUCCESS"
    assert s["prompt"] == "SOLVE demo" and s["plan"] == "COMPUTE answer"
    assert 'print("WITNESS' in s["code_snippet"]
    assert s["witness"]["data"] == {"answer": 42}
    assert s["logs"] and s["result"]["ground_truth_grade"]["grade"] == "PASS"


def test_idle_when_nothing_exists(tmp_path):
    s = read_session(latest_session_dir(tmp_path))
    assert s["stage"] == "IDLE" and s["active"] is False


def test_run_and_catalogue_readers(tmp_path):
    root = _make_root(tmp_path)
    run = read_run(root, "run-20260101-000000")
    assert run["results"][0]["grade"] == "PASS"
    assert run["results"][0]["path"] == "catalogue-runs/run-20260101-000000/results/01-01_demo_prompt"
    assert read_run(root, "../../etc") is None
    assert read_catalogue(root)[0]["id"] == "01-01"


def test_http_endpoints_and_path_safety(tmp_path):
    root = _make_root(tmp_path)
    _, server, port = start_server(root, port=0)
    try:
        base = f"http://127.0.0.1:{port}"
        assert server.server_address[0] == "127.0.0.1"  # localhost only

        status, body = _get(base, "/")
        assert status == 200 and b"PDLt Viewer" in body
        assert b"https://" not in body.replace(b"http://127.0.0.1", b"")  # no external CDN

        assert json.loads(_get(base, "/api/status")[1])["session_id"] == "01-01_demo_prompt"
        runs = json.loads(_get(base, "/api/runs")[1])
        assert runs[0]["id"] == "run-20260101-000000" and runs[0]["pass_rate_pct"] == 100.0
        assert json.loads(_get(base, "/api/run?id=run-20260101-000000")[1])["results"][0]["id"] == "01-01"
        assert json.loads(_get(base, "/api/catalogue")[1])[0]["name"] == "demo_prompt"
        assert json.loads(_get(base, "/api/prompt?id=01-01")[1])["text"] == "Solve the demo."

        rel = "catalogue-runs/run-20260101-000000/results/01-01_demo_prompt"
        assert json.loads(_get(base, "/api/status?path=" + rel)[1])["stage"] == "CLOSED_SUCCESS"

        with pytest.raises(urllib.error.HTTPError) as exc:
            _get(base, "/api/status?path=../../../etc")
        assert exc.value.code == 400
        with pytest.raises(urllib.error.HTTPError) as exc:
            _get(base, "/api/run?id=nope")
        assert exc.value.code == 404
    finally:
        server.shutdown()
        server.server_close()


def test_requests_for_another_host_are_refused(tmp_path):
    """DNS rebinding: a page on another site that resolves its own name to 127.0.0.1
    must not read sessions and transcripts through the viewer."""
    root = _make_root(tmp_path)
    _, server, port = start_server(root, port=0)
    try:
        base = f"http://127.0.0.1:{port}"
        request = urllib.request.Request(base + "/api/status", headers={"Host": f"attacker.example:{port}"})
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(request)
        assert exc.value.code == 403
        for host in (f"localhost:{port}", f"127.0.0.1:{port}", "LOCALHOST"):
            request = urllib.request.Request(base + "/api/runs", headers={"Host": host})
            with urllib.request.urlopen(request) as resp:
                assert resp.status == 200
    finally:
        server.shutdown()
        server.server_close()


def test_viewer_does_not_import_the_harness():
    text = (Path(__file__).resolve().parents[1] / "viewer" / "server.py").read_text(encoding="utf-8")
    assert "pdl_taskmaster" not in text


def _live_session(root: Path, name: str, mtime: float) -> Path:
    session = root / "runs" / "live-sessions" / name
    deep = session / "workspaces" / "W-1" / "turns" / "turn_001" / "stages"
    deep.mkdir(parents=True)
    log = session / "worker-progress.log"
    log.write_text("[dev:telemetry] controller stage: PROMPT_REVIEW\n", encoding="utf-8")
    for path in (log, session / "workspaces", session):
        os.utime(path, (mtime, mtime))
    return session


def test_latest_session_never_walks_whole_trees(tmp_path, monkeypatch):
    """Polling must not rescan every file of every session (a catalogue holds tens of
    thousands): the newest session is judged from its own top-level entries."""
    root = _make_root(tmp_path)
    old = _live_session(root, "session-old", 1_000_000_000)
    new = _live_session(root, "session-new", 2_000_000_000)
    # A deep write in an old session does not make it newest; its transcript would.
    (old / "workspaces" / "W-1" / "turns" / "turn_001" / "stages" / "deep.json").write_text("{}", encoding="utf-8")

    def no_walk(self, pattern):
        raise AssertionError(f"rglob({pattern!r}) while choosing the latest session")

    monkeypatch.setattr(Path, "rglob", no_walk)
    assert latest_session_dir(root) == new
    os.utime(old / "worker-progress.log", (3_000_000_000, 3_000_000_000))
    assert latest_session_dir(root) == old


def test_concurrent_polls_share_one_computation(tmp_path, monkeypatch):
    """A page polling faster than the disk answers must not pile up work: polls that
    arrive during a computation wait for it and get its answer."""
    from viewer import server as viewer_server

    root = _make_root(tmp_path)
    calls = []
    real = viewer_server.read_session

    def slow_read(target):
        calls.append(target)
        time.sleep(0.3)
        return real(target)

    monkeypatch.setattr(viewer_server, "read_session", slow_read)
    _, server, port = start_server(root, port=0)
    try:
        base = f"http://127.0.0.1:{port}"
        results = []
        threads = [threading.Thread(target=lambda: results.append(json.loads(_get(base, "/api/status")[1])))
                   for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert len(results) == 8 and len(calls) == 1
        assert all(r["session_id"] == "01-01_demo_prompt" and "activity" in r for r in results)
    finally:
        server.shutdown()
        server.server_close()


def test_transcript_tail_reads_only_the_end(tmp_path):
    from viewer.server import LOG_TAIL_LINES, _tail_lines

    path = tmp_path / "transcript.txt"
    path.write_text("".join(f"line {i:06d} " + "x" * 40 + "\n" for i in range(20_000)), encoding="utf-8")
    lines = _tail_lines(path, LOG_TAIL_LINES)
    assert len(lines) == LOG_TAIL_LINES
    assert lines[-1].startswith("line 019999") and lines[0].startswith("line 019800")
    assert _tail_lines(path, 5, max_bytes=120) == [f"line {i:06d} " + "x" * 40 for i in (19998, 19999)]


def test_page_polls_without_overlap_and_backs_off_when_hidden():
    html = (Path(__file__).resolve().parents[1] / "viewer" / "index.html").read_text(encoding="utf-8")
    assert "setInterval" not in html  # a fixed interval keeps firing while a slow answer is pending
    assert "visibilitychange" in html and "document.hidden" in html


def test_followed_status_is_reread_after_its_max_age(tmp_path, monkeypatch):
    """A change deep in the followed session (no top-level entry touched) still shows
    up: the payload is reread from disk once it is older than the max age."""
    from viewer import server as viewer_server

    root = _make_root(tmp_path)
    calls = []
    real = viewer_server.read_session
    monkeypatch.setattr(viewer_server, "read_session", lambda target: calls.append(target) or real(target))
    clock = [1000.0]
    monkeypatch.setattr(viewer_server.time, "monotonic", lambda: clock[0])
    cache = viewer_server._StatusCache(root)
    cache.get()
    for step in (2.0, 2.0, 2.0, 2.0):  # unchanged session, polled every 2 s
        clock[0] += step
        cache.get()
    assert len(calls) == 1
    clock[0] += 3.0  # 11 s since the read
    cache.get()
    assert len(calls) == 2
