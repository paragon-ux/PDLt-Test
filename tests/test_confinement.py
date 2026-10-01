"""Session-scoped confinement of model-authored programs (ADR-0021).

Lifecycle: one session root per sandbox outside every referee-read tree, a fresh
directory per run, release on close(), and a sweep of roots whose host was killed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from pdl_taskmaster.verification import sandbox as sb
from pdl_taskmaster.verification.sandbox import ExecutionSandbox

ROOT = Path(__file__).resolve().parents[1]


def _dead_pid() -> int:
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


# -- lifecycle ---------------------------------------------------------------------


def test_session_root_is_outside_the_repository_and_holds_an_owner_record():
    with ExecutionSandbox(label="lifecycle") as sandbox:
        assert sandbox.session_info is None  # built lazily, on the first run
        result = sandbox.run_code("import os\nprint(os.getcwd())")
        assert result.success, result.stderr
        root = Path(sandbox.session_info["root"])
        assert root.parent == sb.sandbox_base_dir().resolve()
        assert not root.is_relative_to(ROOT)
        cwd = Path(result.stdout.strip())
        assert cwd.parent == root / "work" and cwd.name.startswith("run-")
        owner = json.loads((root / sb.OWNER_FILENAME).read_text(encoding="utf-8"))
        assert owner["pid"] == os.getpid() and owner["backend"] == sandbox.backend_name
    assert not root.exists()


def test_each_run_starts_in_a_fresh_empty_directory():
    with ExecutionSandbox() as sandbox:
        first = sandbox.run_code(
            "import os\nopen('left.txt', 'w').write('x')\nos.mkdir('sub')\nprint(sorted(os.listdir('.')))"
        )
        assert first.success, first.stderr
        second = sandbox.run_code("import os\nprint(sorted(os.listdir('.')))")
        assert second.success, second.stderr
        assert "left.txt" in first.stdout
        assert second.stdout.strip() == "['_entry.py', 'program.py', 'tmp']"
        work = Path(sandbox.session_info["root"]) / "work"
        assert list(work.iterdir()) == []  # nothing survives a run


def test_temporary_files_land_inside_the_run_directory():
    with ExecutionSandbox() as sandbox:
        result = sandbox.run_code(
            "import os, tempfile\n"
            "fd, name = tempfile.mkstemp(); os.close(fd)\n"
            "print(os.path.dirname(name) == os.path.join(os.getcwd(), 'tmp'))"
        )
        assert result.success, result.stderr
        assert result.stdout.strip() == "True"


def test_close_is_idempotent_and_a_closed_sandbox_can_run_again():
    sandbox = ExecutionSandbox()
    assert sandbox.run_code("print(1)").success
    first_root = Path(sandbox.session_info["root"])
    sandbox.close()
    sandbox.close()
    assert not first_root.exists() and sandbox.session_info is None
    assert sandbox.run_code("print(2)").stdout == "2\n"
    assert Path(sandbox.session_info["root"]) != first_root
    sandbox.close()


def test_stale_sweep_removes_roots_whose_owner_is_gone(tmp_path):
    stale = tmp_path / "engine-stale"
    live = tmp_path / "engine-live"
    foreign = tmp_path / "engine-foreign"
    for root, pid, host in ((stale, _dead_pid(), None), (live, os.getppid(), None), (foreign, _dead_pid(), "elsewhere")):
        (root / "work").mkdir(parents=True)
        owner = {"pid": pid, "backend": "test"}
        if host:
            owner["host"] = host
        (root / sb.OWNER_FILENAME).write_text(json.dumps(owner), encoding="utf-8")
    released = []
    removed = sb.sweep_stale_roots(tmp_path, cleanup=lambda root, owner: released.append(owner["backend"]))
    assert removed == [stale]
    assert not stale.exists() and live.exists() and foreign.exists()
    assert released == ["test"]


def test_stale_sweep_leaves_a_root_being_created(tmp_path):
    (tmp_path / "engine-new").mkdir()  # no owner record yet
    assert sb.sweep_stale_roots(tmp_path) == []


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX process groups")
def test_interrupted_host_leaves_no_orphaned_program(monkeypatch):
    started: list[subprocess.Popen] = []
    real_communicate = subprocess.Popen.communicate

    def interrupted(self, *args, **kwargs):
        if self not in started:
            started.append(self)
            time.sleep(0.5)  # the program is running
            raise KeyboardInterrupt
        return real_communicate(self, *args, **kwargs)

    monkeypatch.setattr(subprocess.Popen, "communicate", interrupted)
    with ExecutionSandbox(timeout_seconds=30) as sandbox:
        with pytest.raises(KeyboardInterrupt):
            sandbox.run_code("import time\ntime.sleep(60)")
        assert sandbox.session_info is not None
    assert started and started[0].wait(timeout=5) is not None  # killed, not orphaned


def test_engine_logs_the_sandbox_session_once_per_workspace(tmp_path):
    from pdl_taskmaster.runtime.session_engine import SessionEngine

    engine = SessionEngine(ROOT, lambda r: "", workspace_root=tmp_path, sys1_client=None)
    engine.workspace = engine._new_workspace()
    engine._run_deliverable_code("```python\nprint(1)\n```\n```python\nprint(2)\n```")
    events_file = next(engine.workspace.path.rglob("events.jsonl"))
    events = [json.loads(line) for line in events_file.read_text(encoding="utf-8").splitlines()]
    kinds = [e["kind"] for e in events]
    assert kinds.count("SANDBOX_SESSION") == 1 and kinds.count("SANDBOX_RUN") == 2
    session = next(e for e in events if e["kind"] == "SANDBOX_SESSION")["payload"]
    root = Path(session["root"])
    assert not root.is_relative_to(tmp_path)
    assert all(e["payload"]["backend"] == session["backend"] for e in events if e["kind"] == "SANDBOX_RUN")
    engine.close()
    assert not root.exists()


def test_host_close_releases_the_engine_sandbox(tmp_path):
    from pdl_taskmaster.host.app import PDLtHost

    host = PDLtHost(ROOT, worker=object(), workspace_root=tmp_path).start()
    assert host.engine.sandbox.run_code("print(1)").success
    root = Path(host.engine.sandbox.session_info["root"])
    host.close()
    assert not root.exists()
