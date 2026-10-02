from __future__ import annotations

import os
import sys
import tempfile
import pytest
from pathlib import Path

from pdl_taskmaster.verification.sandbox import ExecutionSandbox, SandboxResult


def test_sandbox_success_execution():
    sandbox = ExecutionSandbox(timeout_seconds=5.0)
    result = sandbox.run_code("print('HELLO FROM SANDBOX')")
    assert result.success
    assert result.exit_code == 0
    assert "HELLO FROM SANDBOX" in result.stdout
    assert not result.timed_out
    assert not result.oom_killed
    assert result.duration_ms > 0.0


def test_sandbox_timeout_termination():
    sandbox = ExecutionSandbox(timeout_seconds=0.5)
    # An infinite loop must be terminated by the sandbox
    result = sandbox.run_code("import time\nwhile True:\n    time.sleep(0.05)")
    assert not result.success
    assert result.timed_out
    assert result.exit_code in (124, 1, -1)


def test_sandbox_memory_limit_oom():
    # 50 MB limit, attempting 120 MB allocation
    sandbox = ExecutionSandbox(timeout_seconds=5.0, memory_limit_bytes=50 * 1024 * 1024)
    result = sandbox.run_code("x = bytearray(120 * 1024 * 1024)\nprint(len(x))")
    assert not result.success
    assert result.oom_killed
    assert result.exit_code != 0


def test_sandbox_network_blocking():
    # Default sandbox forbids network access
    sandbox = ExecutionSandbox(allow_network=False)
    code = """
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 9))
"""
    result = sandbox.run_code(code)
    assert not result.success
    assert result.exit_code != 0
    assert "Network access is strictly disabled" in result.stderr or "PermissionError" in result.stderr


def test_sandbox_scratchpad_cleanup():
    sandbox = ExecutionSandbox()
    test_marker = "sandbox_scratchpad_test_marker.txt"
    code = f"""
with open({test_marker!r}, "w") as f:
    f.write("temporary data")
print("WROTE_FILE")
"""
    result = sandbox.run_code(code)
    assert result.success
    assert "WROTE_FILE" in result.stdout
    # Verify file is not in current working dir
    assert not Path(test_marker).exists()


def test_sandbox_low_overhead():
    # Verify execution overhead is minimal
    sandbox = ExecutionSandbox()
    result = sandbox.run_code("x = 1 + 1\nprint(x)")
    assert result.success
    assert "2" in result.stdout.strip()
    # Python startup + Windows Job Object assignment should complete promptly
    assert result.duration_ms < 2500.0
    # Native confinement is built once per session; per run it adds at most 50 ms
    # (median) over the audit-only opt-out on the same host.
    native = ExecutionSandbox(mode="native")
    if native.probe():
        import statistics

        medians = {}
        for mode, box in (("native", native), ("audit-only", ExecutionSandbox(mode="audit-only"))):
            with box:
                box.run_code("pass")  # session setup, not per-run overhead
                medians[mode] = statistics.median(box.run_code("x = 1 + 1").duration_ms for _ in range(9))
        assert medians["native"] - medians["audit-only"] <= 50.0, medians


def test_sandbox_env_has_no_secrets(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-secret-value")
    monkeypatch.setenv("SYS1_API_KEY", "sk-test-secret-value-2")
    result = ExecutionSandbox().run_code("import os\nprint(sorted(os.environ))")
    assert result.success, result.stderr
    assert "OPENROUTER_API_KEY" not in result.stdout
    assert "SYS1_API_KEY" not in result.stdout
    assert "sk-test-secret" not in result.stdout


def test_sandbox_blocks_network_and_process_creation():
    sandbox = ExecutionSandbox()
    for code in (
        "import socket\nsocket.create_connection(('127.0.0.1', 9))",
        "import _socket\ns = _socket.socket()\ns.connect(('127.0.0.1', 9))",
        "import subprocess\nsubprocess.run(['echo', 'hi'])",
        "import os\nos.system('echo hi')",
    ):
        result = sandbox.run_code(code)
        assert not result.success, code
        assert "PermissionError" in result.stderr, (code, result.stderr)


def test_sandbox_allow_network_skips_prelude():
    result = ExecutionSandbox(allow_network=True).run_code("import subprocess\nprint('ok')")
    assert result.success


def test_sandbox_unicode_output_is_utf8_on_every_os():
    """-I ignores PYTHONIOENCODING: without -X utf8 a Windows child writes the ANSI
    code page and crashes on characters it cannot encode."""
    text = "café ✓ 漢字 \U0001f600"
    result = ExecutionSandbox().run_code(f"import sys\nprint({text!r})\nprint({text!r}, file=sys.stderr)")
    assert result.success, result.stderr
    assert result.stdout == text + "\n"
    assert text in result.stderr


def test_sandbox_output_uses_lf_line_endings_on_every_os():
    result = ExecutionSandbox().run_code("print('a')\nprint('b')")
    assert result.success, result.stderr
    assert result.stdout == "a\nb\n"


def test_sandbox_timeout_keeps_output_printed_before_the_kill():
    """Unbuffered streams (-u): output printed before a timeout is not lost in the
    child's buffer when the host kills it."""
    result = ExecutionSandbox(timeout_seconds=1.0).run_code("import time\nprint('partial result')\ntime.sleep(30)")
    assert result.timed_out
    assert "partial result" in result.stdout


@pytest.mark.parametrize("step_limit", [None, 100_000])
def test_sandbox_program_may_use_future_imports(step_limit):
    """The preludes run before the program but never in its source: a program's own
    `from __future__` import stays its first statement."""
    code = '"""Docstring."""\nfrom __future__ import annotations\ndef f(x: Undefined) -> None: ...\nprint("ok")'
    result = ExecutionSandbox().run_code(code, step_limit=step_limit)
    assert result.success, result.stderr
    assert result.stdout.strip() == "ok"


def test_sandbox_withholds_arbitrary_secret_variables(monkeypatch):
    monkeypatch.setenv("PDLT_TEST_FAKE_TOKEN", "fake-secret-7f3a9c")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "fake-secret-aws-1b2c")
    result = ExecutionSandbox().run_code("import os\nprint(dict(os.environ))")
    assert result.success, result.stderr
    assert "fake-secret" not in result.stdout
    assert "PDLT_TEST_FAKE_TOKEN" not in result.stdout


def test_sandbox_blocks_unconnected_datagram_send():
    import socket

    if not hasattr(socket.socket, "sendmsg"):
        pytest.skip("socket.sendmsg is not available on this platform")
    code = (
        "import socket\ns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)\n"
        "s.sendmsg([b'x'], [], 0, ('127.0.0.1', 9))"
    )
    result = ExecutionSandbox().run_code(code)
    assert not result.success
    assert "PermissionError" in result.stderr, result.stderr


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX resource limits")
def test_sandbox_sets_a_cpu_time_backstop_on_posix():
    """A program orphaned by a killed host is outside the host's process group and
    timeout; the kernel's CPU-time limit still stops it."""
    result = ExecutionSandbox(timeout_seconds=2.0).run_code(
        "import resource\nprint(resource.getrlimit(resource.RLIMIT_CPU)[0])"
    )
    assert result.success, result.stderr
    assert int(result.stdout) == 5  # ceil(2 x 2.0 s) + 1


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only environment and process APIs")
def test_sandbox_windows_environment_keeps_what_python_needs():
    code = (
        "import os, tempfile\n"
        "assert os.environ.get('SYSTEMROOT')\n"
        "os.urandom(16)\n"
        "fd, name = tempfile.mkstemp(); os.close(fd); os.unlink(name)\n"
        "print('ok')"
    )
    result = ExecutionSandbox().run_code(code)
    assert result.success, result.stderr
    assert result.stdout == "ok\n"


@pytest.mark.skipif(sys.platform != "win32", reason="os.startfile is Windows-only")
def test_sandbox_blocks_startfile_on_windows():
    result = ExecutionSandbox().run_code("import os\nos.startfile('cmd.exe')")
    assert not result.success
    # The audit hook denies it (PermissionError), unless ShellExecute is unavailable
    # in the AppContainer: os.startfile then raises NotImplementedError before
    # the audit event fires. Either way nothing was launched.
    assert "PermissionError" in result.stderr or (
        "NotImplementedError: startfile not available" in result.stderr
    ), result.stderr


@pytest.mark.skipif(sys.platform != "win32", reason="Windows exit statuses")
def test_sandbox_windows_oom_exit_status_is_unsigned():
    from pdl_taskmaster.verification import sandbox as sb

    assert 0xC0000017 in sb._WINDOWS_OOM_EXIT_CODES
    result = ExecutionSandbox().run_code("import os\nos._exit(-1073741801)")  # signed form of 0xC0000017
    assert result.exit_code == 0xC0000017
    assert result.oom_killed
