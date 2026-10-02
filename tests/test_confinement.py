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


# -- backend selection and fail-closed ---------------------------------------------

from pdl_taskmaster.verification.confinement import backends as cb  # noqa: E402
from pdl_taskmaster.verification.confinement import policy as cp  # noqa: E402


def test_mode_comes_from_the_argument_then_the_environment(monkeypatch):
    monkeypatch.delenv("PDLT_SANDBOX", raising=False)
    assert cb.resolve_mode(None) == "auto"
    monkeypatch.setenv("PDLT_SANDBOX", "Audit-Only")
    assert cb.resolve_mode(None) == "audit-only"
    assert cb.resolve_mode("native") == "native"
    assert ExecutionSandbox().backend_name == "audit-only"


def test_an_unknown_mode_fails_closed():
    with ExecutionSandbox(mode="bogus") as sandbox:
        assert not sandbox.probe()
        result = sandbox.run_code("print('ran')")
        assert result.error.startswith("sandbox_unavailable:") and "unknown sandbox mode" in result.error
        assert result.stdout == "" and not result.success
        assert sandbox.session_info == {"backend": "bogus", "mode": "bogus", "available": False,
                                        "reason": sandbox.unavailable_reason}


def test_a_backend_that_cannot_apply_runs_nothing(monkeypatch, tmp_path):
    marker = tmp_path / "ran.txt"
    monkeypatch.setattr(cb, "_native_backend", lambda: cb.UnavailableBackend("native", "forced for the test"))
    with ExecutionSandbox(mode="native") as sandbox:
        result = sandbox.run_code(f"open({str(marker)!r}, 'w').write('x')")
        assert result.error == "sandbox_unavailable:forced for the test"
        assert sandbox._session is None  # no session root was created
    assert not marker.exists()


def test_a_backend_whose_setup_fails_runs_nothing(monkeypatch):
    class Failing(cb.Backend):
        name = "failing"

        def prepare(self, policy, session):
            raise RuntimeError("setup exploded")

    monkeypatch.setattr(cb, "_native_backend", Failing)
    before = set(sb.sandbox_base_dir().iterdir())
    with ExecutionSandbox(mode="native", label="failing") as sandbox:
        result = sandbox.run_code("print('ran')")
        assert result.error == "sandbox_unavailable:failing setup failed: setup exploded"
        assert not sandbox.probe()  # stays unavailable for the session
        assert not [p for p in set(sb.sandbox_base_dir().iterdir()) - before if p.name.startswith("failing-")]


def test_unavailable_execution_is_described_truthfully():
    sandbox = ExecutionSandbox(mode="bogus")
    tools = sandbox.describe(sb.DEFAULT_BUDGET)
    assert tools[0]["description"].startswith("Unavailable in this session")
    assert "not executed" in tools[0]["description"]
    assert sandbox.decision_state()["execution_environment"].startswith("No program execution is available")


def test_engine_reports_sandbox_unavailable_and_runs_no_later_block(tmp_path):
    from pdl_taskmaster.runtime.session_engine import SessionEngine
    from pdl_taskmaster.verification.error_registry import finding_codes

    engine = SessionEngine(ROOT, lambda r: "", workspace_root=tmp_path, sys1_client=None, sandbox_mode="bogus")
    engine.workspace = engine._new_workspace()
    assert engine.available_execution_tools[0]["description"].startswith("Unavailable in this session")
    witness, failures = engine._run_deliverable_code("```python\nprint(1)\n```\n```python\nprint(2)\n```")
    assert witness is None and finding_codes(failures) == ["SANDBOX_UNAVAILABLE"]
    assert "unknown sandbox mode" in failures[0]
    events = list(engine.workspace._events)
    session = next(e for e in events if e["kind"] == "SANDBOX_SESSION")["payload"]
    assert session["available"] is False and session["backend"] == "bogus"
    assert [e["payload"]["block"] for e in events if e["kind"] == "SANDBOX_RUN"] == [1]
    engine.close()


def test_sandbox_unavailable_is_not_repaired(tmp_path):
    from test_execution_phase import _run_raising

    witness = {"kind": "RESULT", "result_ir": {},
               "body": "import json\nprint('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'x': 1}}))"}
    engine, response, executes, events = _run_raising(
        tmp_path, [witness] * 3, sandbox=ExecutionSandbox(mode="bogus"),
    )
    assert len(executes) == 1  # the environment does not change between attempts
    failed = next(e for e in events if e["kind"] == "VERIFICATION_FAILED")["payload"]
    assert "SANDBOX_UNAVAILABLE" in failed["codes"]
    assert "Unavailable in this session" in executes[0].prompt


def test_audit_only_runs_with_a_loud_warning(capsys, tmp_path):
    from pdl_taskmaster.host.app import PDLtHost
    from pdl_taskmaster.host.repl import _announce_sandbox

    host = PDLtHost(ROOT, worker=object(), workspace_root=tmp_path, sandbox_mode="audit-only").start()
    _announce_sandbox(host)
    assert "WARNING: --sandbox audit-only" in capsys.readouterr().out
    assert host.engine.sandbox.run_code("print('ran')").stdout == "ran\n"
    assert host.engine.sandbox.session_info["backend"] == "audit-only"
    host.close()


def test_unavailable_native_backend_is_announced(capsys, tmp_path):
    from pdl_taskmaster.host.app import PDLtHost
    from pdl_taskmaster.host.repl import _announce_sandbox

    host = PDLtHost(ROOT, worker=object(), workspace_root=tmp_path, sandbox_mode="bogus").start()
    _announce_sandbox(host)
    out = capsys.readouterr().out
    assert out.startswith("[warn] code execution unavailable: unknown sandbox mode")
    assert "--sandbox container" in out and "--sandbox audit-only" in out
    host.close()


def test_runner_passes_the_sandbox_mode_to_the_harness(tmp_path):
    import run_catalogue

    cmd = run_catalogue.build_harness_command(tmp_path / "p.txt", "s", tmp_path / "t", tmp_path / "d", "m", "low",
                                              (), {"sandbox": "audit-only"})
    assert cmd[cmd.index("--sandbox") + 1] == "audit-only"
    assert "--sandbox" not in run_catalogue.build_harness_command(tmp_path / "p.txt", "s", tmp_path / "t",
                                                                   tmp_path / "d", "m", "low")


def test_policy_reads_only_the_base_install_and_system_libraries(tmp_path):
    (tmp_path / "work").mkdir()
    policy = cp.build_policy(tmp_path, tmp_path / "work")
    home = Path.home().resolve()
    assert policy.write_roots == ((tmp_path / "work").resolve(),)
    assert policy.interpreter == cp.base_interpreter() and policy.interpreter.is_absolute()
    for root in policy.read_roots:
        assert not ROOT.is_relative_to(root), root  # never the repository
        assert not home.is_relative_to(root), root  # never the home directory
        assert not str(root).startswith("/proc"), root
    assert not policy.network and not policy.processes


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="ELF executables")
def test_policy_grants_execute_on_the_interpreter_and_its_loader_only():
    loader = cp.elf_interpreter(cp.base_interpreter())
    assert loader is not None and loader.exists() and "ld" in loader.name
    policy = cp.build_policy(Path("/tmp"), Path("/tmp"))
    assert policy.exec_paths == (cp.base_interpreter(), loader)


# -- escape suite: every backend available on this host ------------------------------
#
# Each case runs under the full configuration (audit hook on) and, for native
# backends, with the audit hook switched off: the OS-native layer must hold on its
# own. Backends this host cannot run are skipped with the reason (the Windows and
# macOS legs run in CI, .github/workflows/sandbox.yml).

import secrets  # noqa: E402
import socket  # noqa: E402
import tempfile  # noqa: E402
import threading  # noqa: E402

_IS_WINDOWS = sys.platform == "win32"
_MODES = ["native", "container", "audit-only"]


_AVAILABLE: dict[str, str | None] = {}


def _require(mode: str) -> None:
    """Skip when this host cannot run the backend, unless CI requires it
    (PDLT_REQUIRE_BACKENDS=native,container): then the test fails instead."""
    if mode not in _AVAILABLE:
        with ExecutionSandbox(mode=mode) as sandbox:
            # A real run: a container runtime can answer and still fail to start the image.
            result = sandbox.run_code("pass") if sandbox.probe() else None
            _AVAILABLE[mode] = sandbox.unavailable_reason if result is None or result.error else None
    reason = _AVAILABLE[mode]
    if reason is not None:
        required = {m.strip() for m in os.environ.get("PDLT_REQUIRE_BACKENDS", "").split(",")}
        if mode in required:
            pytest.fail(f"{mode} backend required by PDLT_REQUIRE_BACKENDS but unavailable: {reason}")
        pytest.skip(f"{mode} backend unavailable on this host: {reason}")


@pytest.fixture(params=_MODES)
def mode(request):
    _require(request.param)
    return request.param


@pytest.fixture(params=[(m, hooks) for m in _MODES for hooks in (True, False) if hooks or m != "audit-only"],
                ids=lambda p: f"{p[0]}-{'hooks' if p[1] else 'native-only'}")
def configuration(request):
    _require(request.param[0])
    return request.param


def _blocked(configuration, result) -> bool:
    """Denied with PermissionError, by the audit hook or the native layer. Inside a
    container without the hook, a host path simply does not exist there (or the
    root is read-only): only the host-side effect, asserted by each test, counts."""
    mode, hooks = configuration
    return _denied(result) or (mode == "container" and not hooks)


def _open(configuration, **kwargs) -> ExecutionSandbox:
    mode, hooks = configuration
    sandbox = ExecutionSandbox(mode=mode, label="escape", **kwargs)
    if not hooks:
        sandbox._policy_hooks = False  # the test-only switch: native layer alone
    return sandbox


def test_escape_writing_outside_the_run_directory_is_denied(configuration, tmp_path):
    token = secrets.token_hex(4)
    workspace = tmp_path / "session" / "workspaces" / "W-0001"
    workspace.mkdir(parents=True)
    targets = [
        Path.home() / f"pdlt-escape-{token}.txt",
        ROOT / f"pdlt-escape-{token}.txt",
        workspace / f"pdlt-escape-{token}.txt",
        Path(tempfile.gettempdir()) / f"pdlt-escape-{token}.txt",
        sb.sandbox_base_dir() / f"pdlt-escape-{token}.txt",
    ]
    try:
        with _open(configuration) as sandbox:
            for target in targets:
                result = sandbox.run_code(f"open({str(target)!r}, 'w').write('escaped')")
                assert _blocked(configuration, result), (target, result.stderr)
                assert not target.exists(), target
    finally:
        for target in targets:
            target.unlink(missing_ok=True)


def test_escape_reading_a_secret_outside_is_denied(configuration, secret):
    with _open(configuration) as sandbox:
        for code in (f"print(open({str(secret)!r}).read())",
                     f"import os\nprint(os.read(os.open({str(secret)!r}, os.O_RDONLY), 100))",
                     f"import os\nprint(os.listdir({str(secret.parent)!r}))"):
            result = sandbox.run_code(code)
            assert _blocked(configuration, result), (code, result.stderr)
            assert not result.success
            assert "top-secret-value" not in result.stdout and "secret.txt" not in result.stdout


def test_escape_following_a_link_that_points_outside_is_denied(configuration, secret):
    code = f"import os\nos.symlink({str(secret)!r}, 'link')\nprint(open('link').read())"
    with _open(configuration) as sandbox:
        result = sandbox.run_code(code)
    # Denied at the link (audit hook; or WinError 1314 in an AppContainer) or at the read.
    assert not result.success, result.stderr
    assert "PermissionError" in result.stderr or "1314" in result.stderr or _blocked(configuration, result)
    assert "top-secret-value" not in result.stdout


def test_escape_native_code_cannot_read_the_secret_without_the_audit_hook(mode, secret):
    """With the audit hook off, ctypes loads: only the native layer stands."""
    if mode == "audit-only":
        pytest.skip("audit-only has no native layer")
    if _IS_WINDOWS:
        opener = "ctypes.cdll.msvcrt._open"
    else:
        opener = "ctypes.CDLL(None).open"
    code = (
        "import ctypes, os\n"
        f"fd = {opener}({str(secret).encode()!r}, 0)\n"
        "print('fd', fd)\n"
        "print(os.read(fd, 100) if fd >= 0 else 'denied')\n"
    )
    with _open((mode, False)) as sandbox:
        result = sandbox.run_code(code)
    assert result.success, result.stderr  # ctypes itself loaded: the hook was off
    assert "denied" in result.stdout and "top-secret-value" not in result.stdout


def test_escape_connecting_to_a_localhost_listener_is_denied(configuration):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(5)
    accepted: list = []

    def accept():
        try:
            accepted.append(listener.accept())
        except OSError:
            pass

    thread = threading.Thread(target=accept, daemon=True)
    thread.start()
    port = listener.getsockname()[1]
    try:
        with _open(configuration) as sandbox:
            result = sandbox.run_code(
                f"import socket\nsocket.create_connection(('127.0.0.1', {port}), timeout=3)\nprint('connected')"
            )
    finally:
        listener.close()
        thread.join(6)
    assert not result.success and "connected" not in result.stdout, result.stderr
    assert not accepted


def test_escape_starting_a_shell_is_denied(configuration):
    mode, hooks = configuration
    if mode == "container" and not hooks:
        pytest.skip("the container is the boundary: a process started inside it stays in it "
                    "(test_container_confines_what_runs_inside_it)")
    shell = os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe") if _IS_WINDOWS else "/bin/sh"
    argv = [shell, "/c", "echo escaped"] if _IS_WINDOWS else [shell, "-c", "echo escaped"]
    if hooks or _IS_WINDOWS:
        code = f"import subprocess\nprint(subprocess.run({argv!r}, capture_output=True, text=True).stdout)"
    else:
        code = f"import os\nos.execv({shell!r}, {argv!r})"
    with _open(configuration) as sandbox:
        result = sandbox.run_code(code)
    assert not result.success, result.stdout
    assert "escaped" not in result.stdout


def test_escape_a_run_never_sees_an_earlier_run(configuration):
    with _open(configuration) as sandbox:
        first = sandbox.run_code(
            "open('mine.txt', 'w').write('x')\n"
            "try:\n    open('../left.txt', 'w').write('x')\nexcept PermissionError:\n    pass\n"
        )
        assert first.success, first.stderr
        second = sandbox.run_code(
            "import os\n"
            "try:\n    print(sorted(os.listdir('..')))\nexcept PermissionError:\n    print('parent denied')\n"
            "print(sorted(os.listdir('.')))"
        )
    assert second.success, second.stderr
    assert "mine.txt" not in second.stdout and "left.txt" not in second.stdout


def test_escape_modifying_a_harness_owned_deliverable_is_denied(configuration, tmp_path):
    current = tmp_path / "session" / "workspaces" / "W-0001" / "turns" / "0001" / "current.md"
    current.parent.mkdir(parents=True)
    current.write_text("harness-owned", encoding="utf-8")
    with _open(configuration) as sandbox:
        for code in (f"open({str(current)!r}, 'a').write('planted')",
                     f"import os\nos.replace('program.py', {str(current)!r})",
                     f"import os\nos.remove({str(current)!r})"):
            result = sandbox.run_code(code)
            assert _blocked(configuration, result) and not result.success, (code, result.stderr)
    assert current.read_text(encoding="utf-8") == "harness-owned"


# -- positive cases: programs still work under every backend -------------------------


def test_backend_runs_standard_library_programs(mode):
    code = (
        "import json, decimal, fractions, itertools, sqlite3\n"
        "db = sqlite3.connect(':memory:')\n"
        "db.execute('create table t (x)'); db.executemany('insert into t values (?)', [(1,), (2,)])\n"
        "total = db.execute('select sum(x) from t').fetchone()[0]\n"
        "print(json.dumps({'sum': total, 'd': str(decimal.Decimal('1.10') + decimal.Decimal('2.20')),\n"
        "                  'f': str(fractions.Fraction(1, 3) * 3), 'p': len(list(itertools.permutations(range(4))))}))"
    )
    with ExecutionSandbox(mode=mode) as sandbox:
        result = sandbox.run_code(code)
    assert result.success, result.stderr
    assert json.loads(result.stdout) == {"sum": 3, "d": "3.30", "f": "1", "p": 24}


def test_backend_allows_reading_and_writing_the_run_directory(mode):
    code = (
        "import os, tempfile\n"
        "with open('data.txt', 'w', encoding='utf-8') as f:\n    f.write('hello')\n"
        "os.makedirs('a/b'); os.replace('data.txt', 'a/b/data.txt')\n"
        "print(open('a/b/data.txt', encoding='utf-8').read())\n"
        "with tempfile.NamedTemporaryFile('w', delete=False) as f:\n    f.write('t')\n"
        "print(os.path.commonpath([f.name, os.getcwd()]) == os.getcwd())"
    )
    with ExecutionSandbox(mode=mode) as sandbox:
        result = sandbox.run_code(code)
    assert result.success, result.stderr
    assert result.stdout.split() == ["hello", "True"]


@pytest.mark.parametrize("step_limit", [None, 100_000])
def test_backend_keeps_utf8_output_and_future_imports(mode, step_limit):
    text = "café ✓ 漢字"
    code = f'"""Doc."""\nfrom __future__ import annotations\ndef f(x: Undefined) -> None: ...\nprint({text!r})'
    with ExecutionSandbox(mode=mode) as sandbox:
        result = sandbox.run_code(code, step_limit=step_limit)
    assert result.success, result.stderr
    assert result.stdout == text + "\n"


@pytest.mark.xfail(sys.version_info >= (3, 12), strict=True,
                   reason="pre-existing: the step budget is not enforced on Python 3.12+ (it fails the same way "
                          "before this change, see test_execution_profile.py::test_step_budget_cannot_be_evaded)")
def test_backend_enforces_the_step_budget(mode):
    with ExecutionSandbox(mode=mode) as sandbox:
        result = sandbox.run_code("while True: pass", step_limit=10_000, timeout=20)
    assert result.step_budget_exceeded and result.steps_used == 10_001


def test_backend_times_out_and_keeps_partial_output(mode):
    with ExecutionSandbox(mode=mode, timeout_seconds=1.5) as sandbox:
        result = sandbox.run_code("import time\nprint('partial result')\ntime.sleep(30)")
        after = sandbox.run_code("print('next run')")
    assert result.timed_out and "partial result" in result.stdout
    assert after.stdout == "next run\n"  # the session survives a killed program


def test_backend_detects_memory_exhaustion(mode):
    if sys.platform == "darwin" and mode != "container":
        pytest.skip("macOS does not enforce RLIMIT_AS (ADR-0021)")
    with ExecutionSandbox(mode=mode, memory_limit_bytes=64 * 1024 * 1024) as sandbox:
        result = sandbox.run_code("x = bytearray(512 * 1024 * 1024)\nprint(len(x))")
    assert result.oom_killed and not result.success


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Landlock is Linux-only")
def test_landlock_ruleset_descriptor_never_reaches_the_program():
    """preexec_fn (which restricts the child) runs before close_fds, and the ruleset
    fd is O_CLOEXEC: the program holds no descriptor beyond its standard streams."""
    _require("native")
    code = (
        "import os\nopen_fds = []\n"
        "for fd in range(3, 256):\n"
        "    try:\n        os.fstat(fd)\n        open_fds.append(fd)\n    except OSError:\n        pass\n"
        "print(open_fds)"
    )
    with ExecutionSandbox(mode="native") as sandbox:
        result = sandbox.run_code(code)
        assert sandbox.session_info["backend"] == "landlock" and sandbox.session_info["abi"] >= 1
    assert result.success, result.stderr
    assert result.stdout.strip() == "[]"


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Landlock is Linux-only")
def test_landlock_close_releases_the_ruleset_descriptor():
    _require("native")
    sandbox = ExecutionSandbox(mode="native")
    assert sandbox.run_code("print(1)").success
    fd = sandbox._session.backend.ruleset_fd
    os.fstat(fd)
    sandbox.close()
    with pytest.raises(OSError):
        os.fstat(fd)


# -- Seatbelt (macOS): profile and command, verified here; the backend runs in CI -----

from pdl_taskmaster.verification.confinement import seatbelt  # noqa: E402


def _policy(tmp_path, **kwargs):
    (tmp_path / "work").mkdir(exist_ok=True)
    (tmp_path / "lib").mkdir(exist_ok=True)
    (tmp_path / "lib" / "file.so").write_bytes(b"")
    return cp.SandboxPolicy(
        session_root=tmp_path,
        write_roots=(tmp_path / "work",),
        read_roots=(tmp_path / "work", tmp_path / "lib", tmp_path / "lib" / "file.so"),
        exec_paths=(Path(sys.executable),),
        **kwargs,
    )


def test_seatbelt_profile_denies_by_default_and_takes_paths_as_parameters(tmp_path):
    profile, params = seatbelt.build_profile(_policy(tmp_path))
    lines = profile.splitlines()
    assert lines[:3] == ["(version 1)", "(deny default)", '(import "system.sb")']
    assert "network" not in profile and "process-fork" not in profile
    assert '(allow process-exec (literal (param "EXEC_0")))' in lines
    assert '(allow file-read* file-map-executable (subpath (param "READ_1")))' in lines
    assert '(allow file-read* file-map-executable (literal (param "READ_2")))' in lines  # a file is a literal
    assert '(allow file-read* file-write* (subpath (param "WRITE_0")))' in lines
    assert params == {"EXEC_0": sys.executable, "READ_0": str(tmp_path / "work"), "READ_1": str(tmp_path / "lib"),
                      "READ_2": str(tmp_path / "lib" / "file.so"), "WRITE_0": str(tmp_path / "work")}
    assert str(tmp_path) not in profile  # never interpolated


def test_seatbelt_profile_grants_network_and_fork_only_when_the_policy_does(tmp_path):
    profile, _ = seatbelt.build_profile(_policy(tmp_path, network=True, processes=True))
    assert "(allow network*)" in profile and "(allow process-fork)" in profile


def test_seatbelt_command_wraps_the_interpreter_argv(tmp_path):
    argv = seatbelt.sandbox_exec_argv("(version 1)\n", {"A_0": "/x y", "B_0": "/z"}, ["/py", "-I", "_entry.py"])
    assert argv == ["/usr/bin/sandbox-exec", "-p", "(version 1)\n", "-D", "A_0=/x y", "-D", "B_0=/z",
                    "/py", "-I", "_entry.py"]


@pytest.mark.skipif(sys.platform == "darwin", reason="checks the off-platform probe")
def test_seatbelt_is_unavailable_off_macos():
    assert "macOS-only" in seatbelt.SeatbeltBackend().probe()


@pytest.mark.skipif(sys.platform != "darwin", reason="Seatbelt is macOS-only (runs in CI)")
def test_seatbelt_is_the_native_backend_on_macos():
    with ExecutionSandbox(mode="native") as sandbox:
        result = sandbox.run_code("import os\nprint(os.getcwd())")
        info = sandbox.session_info
    assert result.success, result.stderr
    assert info["backend"] == "seatbelt" and info["os"].startswith("macOS")
    assert result.stdout.startswith("/private/")  # realpath'd: /var/folders is /private/var/folders


# -- AppContainer (Windows): layouts, attributes and lifecycle logic, verified here; --
# -- the backend itself runs in the Windows CI leg ----------------------------------

import ctypes  # noqa: E402

from pdl_taskmaster.verification.confinement import appcontainer, winproc  # noqa: E402

_X64 = ctypes.sizeof(ctypes.c_void_p) == 8


@pytest.mark.skipif(not _X64, reason="x64 layouts")
def test_win32_structures_have_their_x64_sizes():
    assert ctypes.sizeof(winproc.STARTUPINFOW) == 104
    assert ctypes.sizeof(winproc.STARTUPINFOEXW) == 112
    assert ctypes.sizeof(winproc.PROCESS_INFORMATION) == 24
    assert ctypes.sizeof(winproc.SECURITY_ATTRIBUTES) == 24
    assert ctypes.sizeof(winproc.SECURITY_CAPABILITIES) == 24
    assert ctypes.sizeof(appcontainer.TRUSTEE_W) == 32
    assert ctypes.sizeof(appcontainer.EXPLICIT_ACCESS_W) == 48
    assert winproc.STARTUPINFOW.hStdInput.offset == 80
    assert winproc.STARTUPINFOEXW.lpAttributeList.offset == 104
    assert winproc.SECURITY_CAPABILITIES.CapabilityCount.offset == 16
    assert appcontainer.EXPLICIT_ACCESS_W.Trustee.offset == 16
    assert appcontainer.TRUSTEE_W.ptstrName.offset == 24


def test_proc_thread_attributes_match_winbase():
    assert winproc.PROC_THREAD_ATTRIBUTE_HANDLE_LIST == 0x00020002
    assert winproc.PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES == 0x00020009
    assert winproc.PROC_THREAD_ATTRIBUTE_JOB_LIST == 0x0002000D
    assert winproc.PROC_THREAD_ATTRIBUTE_CHILD_PROCESS_POLICY == 0x0002000E


def test_environment_block_is_sorted_and_double_terminated():
    block = winproc.environment_block({"TMP": "C:\\t", "Path": "C:\\w", "SYSTEMROOT": "C:\\Windows"})
    assert block == "Path=C:\\w\0SYSTEMROOT=C:\\Windows\0TMP=C:\\t\0\0"
    with pytest.raises(ValueError):
        winproc.environment_block({"A=B": "x"})


def test_appcontainer_profile_name_is_bounded_and_clean():
    assert appcontainer.profile_name("engine-ab_c1") == "PDLt.Sandbox.engine-ab-c1"
    assert len(appcontainer.profile_name("x" * 100)) == 64


def test_appcontainer_sweep_trusts_only_the_profile_the_root_derives(tmp_path):
    root = tmp_path / "engine-abc_123"
    assert appcontainer.profile_to_sweep(root, {"profile": "PDLt.Sandbox.engine-abc-123"}) == \
        "PDLt.Sandbox.engine-abc-123"
    assert appcontainer.profile_to_sweep(root, {"profile": "Microsoft.WindowsCalculator"}) is None
    assert appcontainer.profile_to_sweep(root, {}) is None


def test_appcontainer_runs_one_process_per_job_and_records_its_grant_marker():
    assert appcontainer.AppContainerBackend.job_active_process_limit == 1
    marker = appcontainer.grant_marker(Path("C:/Users/me/AppData/Local/Programs/Python/Python312"))
    assert marker.parent == Path.home() / ".pdlt" and marker.name.startswith("appcontainer-read-grant-")


@pytest.mark.skipif(sys.platform == "win32", reason="checks the off-platform probe")
def test_appcontainer_is_unavailable_off_windows():
    assert "Windows-only" in appcontainer.AppContainerBackend().probe()


@pytest.mark.skipif(sys.platform != "win32", reason="AppContainer is Windows-only (runs in CI)")
def test_appcontainer_is_the_native_backend_and_close_deletes_its_profile():
    sandbox = ExecutionSandbox(mode="native")
    result = sandbox.run_code("print('confined')")
    assert result.success, result.stderr
    info = sandbox.session_info
    assert info["backend"] == "appcontainer" and info["profile"].startswith("PDLt.Sandbox.")
    assert info["sid"].startswith("S-1-15-2-")
    owner = json.loads((Path(info["root"]) / sb.OWNER_FILENAME).read_text(encoding="utf-8"))
    assert owner["profile"] == info["profile"]
    sandbox.close()
    sid = ctypes.c_void_p()
    # Deleted: creating it again succeeds (not HRESULT_FROM_WIN32(ERROR_ALREADY_EXISTS)).
    assert appcontainer.userenv().CreateAppContainerProfile(info["profile"], "t", "t", None, 0,
                                                            ctypes.byref(sid)) == 0
    appcontainer.delete_profile(info["profile"])
    appcontainer.advapi32().FreeSid(sid)


# -- container backend ---------------------------------------------------------------

from pdl_taskmaster.verification.confinement import container as cc  # noqa: E402


def test_container_confines_what_runs_inside_it():
    """Without the audit hook a program can start a shell inside the container; the
    shell is still confined by it: no host files, read-only root, no network."""
    _require("container")
    code = (
        "import os, subprocess\n"
        f"print(os.path.exists({str(ROOT)!r}), os.path.exists({str(Path.home())!r} + '/.ssh'))\n"
        "print(subprocess.run(['sh', '-c', 'touch /usr/x 2>&1; cat /proc/net/dev | wc -l'],\n"
        "                     capture_output=True, text=True).stdout)"
    )
    with _open(("container", False)) as sandbox:
        result = sandbox.run_code(code)
    assert result.success, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines[0] == "False False"
    assert "Read-only file system" in result.stdout
    assert lines[-1].strip() == "3"  # two header lines and the loopback interface: no network


_FAKE_RUNTIME = r'''#!{python}
"""A stand-in container runtime: logs each call, keeps containers in a state file,
and runs exec'd programs on the host with /work mapped to the mounted directory."""
import json, os, subprocess, sys

log, state_path = os.environ["FAKE_RUNTIME_LOG"], os.environ["FAKE_RUNTIME_STATE"]
args = sys.argv[1:]
with open(log, "a") as handle:
    handle.write(json.dumps(args) + "\n")
state = json.load(open(state_path)) if os.path.exists(state_path) else {{"containers": {{}}}}
def save():
    json.dump(state, open(state_path, "w"))
if args[0] == "version":
    print("99.0")
elif args[0] == "run":
    labels = dict(a.split("=", 1) for i, a in enumerate(args) if i and args[i - 1] == "--label")
    mount = next(a for i, a in enumerate(args) if i and args[i - 1] == "-v").rsplit(":/work", 1)[0]
    state["containers"]["fakecid0001"] = {{"labels": labels, "mount": mount}}
    save()
    print("fakecid0001")
elif args[0] == "ps":
    print("\n".join(state["containers"]))
elif args[0] == "inspect":
    fmt, cid = args[2], args[3]
    info = state["containers"].get(cid, {{"labels": {{}}}})
    if "Labels" in fmt:
        print(info["labels"].get(fmt.split('"')[1], ""))
    else:
        print("sha256:fakeimage")
elif args[0] == "image":
    print("python@sha256:fakeimage")
elif args[0] == "rm":
    state["containers"].pop(args[-1], None)
    save()
elif args[0] == "exec":
    rest, env, cwd = args[1:], {{"PATH": os.environ.get("PATH", "")}}, None
    while rest[0] in ("-w", "-e"):
        if rest[0] == "-w":
            cwd = rest[1]
        else:
            key, value = rest[1].split("=", 1)
            env[key] = value
        rest = rest[2:]
    mount = state["containers"][rest[0]]["mount"]
    command = rest[1:]
    if command[:1] == ["sh"]:
        sys.exit(0)
    assert command[:3] == ["timeout", "-s", "KILL"] and command[4] == "python", command
    host = lambda v: v.replace("/work", mount, 1) if v.startswith("/work") else v
    env = {{k: host(v) for k, v in env.items()}}
    sys.exit(subprocess.run([sys.executable] + command[5:], cwd=host(cwd), env=env).returncode)
'''


@pytest.fixture
def fake_runtime(tmp_path, monkeypatch):
    if _IS_WINDOWS:
        pytest.skip("the fake runtime is a POSIX script")
    runtime = tmp_path / "bin" / "docker"
    runtime.parent.mkdir()
    runtime.write_text(_FAKE_RUNTIME.format(python=sys.executable), encoding="utf-8")
    runtime.chmod(0o755)
    log, state = tmp_path / "calls.jsonl", tmp_path / "state.json"
    monkeypatch.setenv("PDLT_CONTAINER_RUNTIME", str(runtime))
    monkeypatch.setenv("FAKE_RUNTIME_LOG", str(log))
    monkeypatch.setenv("FAKE_RUNTIME_STATE", str(state))

    class Fake:
        path = str(runtime)

        @staticmethod
        def calls():
            return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []

        @staticmethod
        def seed(containers):
            state.write_text(json.dumps({"containers": containers}))
    return Fake


def test_container_lifecycle_and_commands_with_a_fake_runtime(fake_runtime):
    sandbox = ExecutionSandbox(mode="container", label="fake")
    assert sandbox.probe()
    result = sandbox.run_code("import os\nprint('hi', os.getcwd().endswith(os.environ['TMPDIR'][-15:-4]))")
    assert result.success, result.stderr
    assert result.stdout == "hi True\n"
    info = sandbox.session_info
    root = Path(info["root"])
    assert info["runtime"] == "docker" and info["container"] == "fakecid0001"
    assert info["image"] == "python:{}.{}-slim".format(*sys.version_info[:2])
    assert info["image_digest"] == "python@sha256:fakeimage"
    owner = json.loads((root / sb.OWNER_FILENAME).read_text())
    assert owner["container"] == "fakecid0001" and owner["runtime"] == fake_runtime.path
    calls = fake_runtime.calls()
    run = next(c for c in calls if c[0] == "run")
    for flag in (["--network", "none"], ["--read-only"], ["--tmpfs", "/tmp"], ["--cap-drop", "ALL"],
                 ["--security-opt", "no-new-privileges"], ["--pids-limit", "64"], ["--memory", "512m"],
                 ["--user", f"{os.getuid()}:{os.getgid()}"], ["--label", f"pdlt.sandbox={root.name}"],
                 ["-v", f"{root / 'work'}:/work"], ["-d", "--rm"]):
        assert any(run[i:i + len(flag)] == flag for i in range(len(run))), flag
    assert run[-3:] == ["python:{}.{}-slim".format(*sys.version_info[:2]), "sleep", "infinity"]
    exec_call = next(c for c in calls if c[0] == "exec" and "timeout" in c)
    assert exec_call[1:3][0] == "-w" and exec_call[2].startswith("/work/run-0001-")
    assert not any(a.startswith("PATH=") for a in exec_call)  # the host PATH stays on the host
    assert exec_call[exec_call.index("fakecid0001"):][:5] == ["fakecid0001", "timeout", "-s", "KILL", "6"]
    assert exec_call[-7:] == ["python", "-I", "-S", "-X", "utf8", "-u", "_entry.py"]
    sandbox.close()
    assert fake_runtime.calls()[-1] == ["rm", "-f", "fakecid0001"]
    assert not root.exists()


def test_container_memory_limit_is_set_inside_the_program(fake_runtime):
    with ExecutionSandbox(mode="container") as sandbox:
        result = sandbox.run_code("import resource\nprint(resource.getrlimit(resource.RLIMIT_AS)[0])",
                                  memory_limit=96 * 1024 * 1024)
    assert result.success, result.stderr
    assert int(result.stdout) == 96 * 1024 * 1024


def test_container_timeout_kills_inside_the_container(fake_runtime):
    with ExecutionSandbox(mode="container", timeout_seconds=1.0) as sandbox:
        result = sandbox.run_code("import time\nprint('partial')\ntime.sleep(20)")
    assert result.timed_out and "partial" in result.stdout
    assert ["exec", "fakecid0001", "sh", "-c", "kill -9 -1 2>/dev/null; true"] in fake_runtime.calls()


def test_container_sweep_removes_only_dead_owners_on_this_host(fake_runtime):
    host = socket.gethostname()
    fake_runtime.seed({
        "stale": {"labels": {"pdlt.sandbox": "s1", "pdlt.owner": f"{host}:{_dead_pid()}"}},
        "live": {"labels": {"pdlt.sandbox": "s2", "pdlt.owner": f"{host}:{os.getppid()}"}},
        "foreign": {"labels": {"pdlt.sandbox": "s3", "pdlt.owner": f"elsewhere:{_dead_pid()}"}},
    })
    assert cc.sweep_stale_containers(fake_runtime.path) == ["stale"]
    assert [c for c in fake_runtime.calls() if c[0] == "rm"] == [["rm", "-f", "stale"]]


def test_container_root_sweep_removes_only_the_container_the_root_started(fake_runtime, tmp_path):
    fake_runtime.seed({"mine": {"labels": {"pdlt.sandbox": "engine-abc"}},
                       "other": {"labels": {"pdlt.sandbox": "engine-xyz"}}})
    cc.ContainerBackend.sweep(tmp_path / "engine-abc", {"runtime": fake_runtime.path, "container": "mine"})
    cc.ContainerBackend.sweep(tmp_path / "engine-abc", {"runtime": fake_runtime.path, "container": "other"})
    cc.ContainerBackend.sweep(tmp_path / "engine-abc", {"runtime": "/bin/sh", "container": "mine"})
    assert [c for c in fake_runtime.calls() if c[0] == "rm"] == [["rm", "-f", "mine"]]


def test_container_exec_maps_paths_and_drops_host_only_variables(tmp_path):
    work = tmp_path / "work"
    argv = cc.exec_argv("docker", "cid", work=work, argv=["/usr/bin/python3", "-I", "_entry.py"],
                        cwd=work / "run-0001-aa", env={"PATH": "/host/bin", "TMPDIR": str(work / "run-0001-aa" / "tmp"),
                                                       "SYSTEMROOT": "C:\\Windows"}, timeout=2.5)
    assert argv == ["docker", "exec", "-w", "/work/run-0001-aa", "-e", "TMPDIR=/work/run-0001-aa/tmp", "cid",
                    "timeout", "-s", "KILL", "4", "python", "-I", "_entry.py"]


def test_container_is_unavailable_without_a_runtime(monkeypatch):
    monkeypatch.setenv("PDLT_CONTAINER_RUNTIME", "/nonexistent/docker")
    assert "no container runtime found" in cc.ContainerBackend().probe()
