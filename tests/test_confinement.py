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


# -- audit layer (every backend) ---------------------------------------------------


def _denied(result) -> bool:
    return not result.success and "PermissionError" in result.stderr


@pytest.fixture
def secret(tmp_path):
    path = tmp_path / "secret.txt"
    path.write_text("top-secret-value", encoding="utf-8")
    return path


@pytest.mark.parametrize("statement", [
    "import ctypes", "import _ctypes", "import ctypes.util", "import cffi", "import _cffi_backend",
])
def test_audit_layer_denies_loading_native_code(statement):
    with ExecutionSandbox() as sandbox:
        result = sandbox.run_code(statement)
    assert _denied(result), result.stderr
    assert "Loading native code is denied" in result.stderr


def test_audit_layer_confines_reads_and_writes(secret, tmp_path):
    with ExecutionSandbox() as sandbox:
        for code in (
            f"open({str(secret)!r}).read()",
            f"open({str(tmp_path / 'planted.txt')!r}, 'w').write('x')",
            f"import os\nos.open({str(tmp_path / 'planted.txt')!r}, os.O_WRONLY | os.O_CREAT)",
            f"import os\nos.listdir({str(tmp_path)!r})",
            f"import os\nos.rename('program.py', {str(tmp_path / 'moved.py')!r})",
            f"import shutil\nshutil.copy({str(secret)!r}, 'copy.txt')",
            f"import os\nos.chdir({str(tmp_path)!r})",
            f"import sqlite3\nsqlite3.connect({str(tmp_path / 'db.sqlite')!r})",
            f"import sqlite3\nsqlite3.connect('file:{(tmp_path / 'db.sqlite').as_posix()}?mode=rwc', uri=True)",
            "open('../escape.txt', 'w').write('x')",
        ):
            result = sandbox.run_code(code)
            assert _denied(result), (code, result.stderr)
    assert not (tmp_path / "planted.txt").exists() and not (tmp_path / "moved.py").exists()


def test_audit_layer_allows_the_run_directory_and_the_standard_library():
    code = (
        "import os, shutil, sqlite3, json\n"
        "assert open(os.__file__, encoding='utf-8').read(10)\n"
        "os.makedirs('a/b')\n"
        "fd = os.open('a', os.O_RDONLY)\n"
        "os.mkdir('c', dir_fd=fd)\n"
        "shutil.copy('program.py', 'a/b/copy.py')\n"
        "os.rename('a/b/copy.py', 'a/b/renamed.py')\n"
        "os.symlink('b', 'a/link')\n"
        "assert os.listdir('a/link') == ['renamed.py']\n"
        "shutil.rmtree('a')\n"
        "sqlite3.connect('local.db').execute('create table t (x)')\n"
        "sqlite3.connect(':memory:').execute('select 1')\n"
        "with open(os.devnull, 'w') as sink:\n"
        "    sink.write('x')\n"
        "print(sorted(os.listdir('.')))"
    )
    with ExecutionSandbox() as sandbox:
        result = sandbox.run_code(code)
    assert result.success, result.stderr
    assert result.stdout.strip() == "['_entry.py', 'local.db', 'program.py', 'tmp']"


@pytest.mark.parametrize("target", ["/", "..", "../..", "sub/../.."])
def test_audit_layer_denies_links_that_leave_their_directory(target):
    with ExecutionSandbox() as sandbox:
        result = sandbox.run_code(f"import os\nos.makedirs('sub', exist_ok=True)\nos.symlink({target!r}, 'link')")
    assert _denied(result), result.stderr


def test_audit_layer_denies_signals():
    with ExecutionSandbox() as sandbox:
        result = sandbox.run_code("import os, signal\nos.kill(os.getppid(), 0)")
    assert _denied(result) and "Signalling other processes" in result.stderr


def test_allowing_network_keeps_process_creation_denied():
    """allow_network once skipped the whole prelude, process checks included."""
    with ExecutionSandbox(allow_network=True) as sandbox:
        result = sandbox.run_code("import os\nos.system('echo hi')")
    assert _denied(result) and "Process creation" in result.stderr


def test_policy_hooks_do_not_count_as_program_steps():
    """The hook runs on every audited event (each open while importing); it is not
    the program's complexity."""
    with ExecutionSandbox() as sandbox:
        result = sandbox.run_code("import json, decimal, fractions\nopen('x', 'w').close()", step_limit=1_000)
    assert result.success, result.stderr
    assert result.steps_used < 200
