from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
ROOT = Path(__file__).resolve().parents[1]

# Recorded fixtures are externalized (repo-restructure-plan §3.1):
# PDLT_FIXTURES_PATH env override -> repo-relative vendored location -> sibling PDL-Standard-Archive.
def _resolve_fixture_file() -> Path:
    env = os.environ.get("PDLT_FIXTURES_PATH", "").strip()
    if env:
        return Path(env) / "recorded-cases.json"
    local = ROOT / "tests" / "fixtures" / "recorded-cases.json"
    if local.is_file():
        return local
    archive = ROOT.parent / "PDL-Standard-Archive" / "fixtures-r4-recorded-worker" / "recorded-cases.json"
    if archive.is_file():
        return archive
    return local

FIXTURE = _resolve_fixture_file()



def _g06_turns() -> list[str]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return fixture["case_turns"]["G06"]


def _run_repl(tmp_path: Path, lines: list[str], session_id: str) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        "-m",
        "pdl_taskmaster.host.repl",
        "--candidate-repo",
        str(ROOT),
        "--worker",
        "recorded",
        "--evidence",
        str(FIXTURE),
        "--case-ids",
        "G06",
        "--workspace-root",
        str(tmp_path / "sessions"),
        "--session-id",
        session_id,
    ]
    return subprocess.run(
        cmd,
        cwd=ROOT,
        input="\n".join(lines) + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )


def test_repl_command_loop_full_deterministic_session(tmp_path: Path) -> None:
    turns = _g06_turns()
    lines = (
        turns
        + ["/status", "/help", "/session", "/worker recorded", "/new"]
        + turns
        + ["/status", "/resume repltest", "/status", "/quit"]
    )
    proc = _run_repl(tmp_path, lines, "repltest")
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out[-3000:]
    assert "PDLt REPL started" in out
    assert "/status -> read-only host state" in out
    assert "worker switched to recorded" in out
    assert "new session:" in out
    assert "resumed session:" in out
    assert out.count("[protocol closed]") >= 2
    assert out.count("CLOSED_SUCCESS") >= 3
    assert "No such file" not in out
    assert "Traceback" not in out
    assert "[error]" not in out  # REPL commands never reach the engine; replay misses never hide
    # First session completed -> durable session pointer exists.
    assert (tmp_path / "sessions" / "repltest" / "session.json").is_file()


def test_new_session_is_lazy_no_fabricated_workspace(tmp_path: Path) -> None:
    proc = _run_repl(tmp_path, ["/new", "/quit"], "lazytest")
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out[-2000:]
    match = re.search(r"new session: (\S+)", out)
    assert match is not None, out
    new_dir = Path(match.group(1))
    assert new_dir.is_dir()
    assert not (new_dir / "session.json").exists(), "pointer must be written lazily after first turn"
    assert not list(new_dir.glob("workspaces/W-*")), "no workspace should be fabricated before a turn"


def test_repl_headless_exit_fail_closed_on_unconfirmed_stage(tmp_path: Path) -> None:
    """ADR-0012 / Kimi pushback: non-interactive runs halting at an unconfirmed stage must exit code 2."""
    turns = _g06_turns()
    # Sending only turn 1 halts at PROMPT_REVIEW_WAIT (unconfirmed review gate)
    proc = _run_repl(tmp_path, turns[:1], "headless_unconfirmed")
    out = proc.stdout + proc.stderr
    assert proc.returncode == 2, out[-2000:]
    assert "[headless halt] Session ended at non-terminal stage" in proc.stderr


def test_headless_review_commands_after_closure_do_not_restart_the_task(tmp_path: Path) -> None:
    """Piped /confirm lines left over after CLOSED_SUCCESS are not a new request (FINDING-19)."""
    proc = _run_repl(tmp_path, _g06_turns() + ["/confirm", "/confirm"], "headless_leftover")
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out[-3000:]
    assert out.count("[protocol closed]") == 1
    assert out.count("No review is open") == 2
    assert "[headless halt]" not in out
    assert "[error]" not in out


def test_review_command_before_any_task_is_not_a_request(tmp_path: Path) -> None:
    proc = _run_repl(tmp_path, ["/confirm", "/quit"], "no_task_confirm")
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out[-3000:]
    assert "No review is open" in out
    assert "[error]" not in out


@pytest.mark.parametrize("command", ["/stop", "/cancel"])
def test_repl_review_cancel_commands_close_cancelled(tmp_path: Path, command: str) -> None:
    """/cancel is engine review vocabulary; the REPL rejected it as an unknown command."""
    turns = _g06_turns()
    proc = _run_repl(tmp_path, turns[:1] + [command], "headless_cancel")
    out = proc.stdout + proc.stderr
    assert "unknown command" not in out
    assert proc.returncode == 1, out[-2000:]  # ADR-0019: CLOSED_CANCELLED
    assert "[protocol closed]" in out


def test_cli_keyboard_interrupt_clean_exit(monkeypatch, capsys) -> None:
    """CLI intercepts KeyboardInterrupt, prints user notice, and exits 130 cleanly without tracebacks."""
    from pdl_taskmaster.host import cli

    def mock_raise(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(cli, "_main_impl", mock_raise)
    code = cli.main([])
    assert code == 130
    captured = capsys.readouterr()
    assert "[session terminated by user]" in captured.err


def test_repl_headless_exit_waiting_input_code_3(monkeypatch, capsys, tmp_path: Path) -> None:
    """Non-interactive runs halting at WAITING_INPUT must exit code 3 (REG-013 / ADR-0019)."""
    from pdl_taskmaster.host import repl

    class MockHost:
        def status(self):
            return {"controller_state": {"stage": "WAITING_INPUT"}}

    class MockRuntime:
        def __init__(self, session_dir):
            self.host = MockHost()
            self.session_dir = session_dir
            self.exit_on_close = True
            transcript_file = session_dir / "transcript.txt"
            self.transcript = transcript_file.open("w", encoding="utf-8")
        def close(self):
            self.transcript.close()

    monkeypatch.setattr(repl, "open_session", lambda *args, **kwargs: MockRuntime(tmp_path))
    def mock_eof(prompt="> "):
        raise EOFError()
    monkeypatch.setattr(repl, "_read_repl_input", mock_eof)
    monkeypatch.setattr(repl, "_disable_bracketed_paste", lambda: None)

    monkeypatch.setattr(sys, "argv", [
        "pdlt",
        "--non-interactive",
        "--candidate-repo", str(ROOT),
        "--evidence", str(FIXTURE),
        "--worker", "recorded",
        "--session-id", "mock-waiting-input",
    ])
    code = repl.main()
    assert code == 3
    captured = capsys.readouterr()
    assert "[headless halt] Session paused at stage 'WAITING_INPUT' (input requested). Exiting (code 3)." in captured.err




def _headless_runtime(monkeypatch, tmp_path: Path, handle, stage: str):
    from types import SimpleNamespace

    from pdl_taskmaster.host import repl

    class MockHost:
        def __init__(self):
            self.engine = SimpleNamespace(
                controller=SimpleNamespace(state=SimpleNamespace(stage=SimpleNamespace(value=stage)))
            )

        def status(self):
            return {"controller_state": {"stage": stage}}

    class MockRuntime:
        def __init__(self, session_dir):
            self.host = MockHost()
            self.session_dir = session_dir
            self.exit_on_close = True
            self.transcript = (session_dir / "transcript.txt").open("w", encoding="utf-8")
            self.handled: list[str] = []

        def handle(self, line):
            self.handled.append(line)
            return handle(line)

        def close(self):
            self.transcript.close()

    runtime = MockRuntime(tmp_path)
    lines = iter(["solve it", "/confirm", "/confirm", "/confirm"])

    def read(prompt="> "):
        try:
            return next(lines)
        except StopIteration:
            raise EOFError()

    monkeypatch.setattr(repl, "open_session", lambda *args, **kwargs: runtime)
    monkeypatch.setattr(repl, "_read_repl_input", read)
    monkeypatch.setattr(repl, "_disable_bracketed_paste", lambda: None)
    monkeypatch.setattr(sys, "argv", [
        "pdlt", "--non-interactive", "--candidate-repo", str(ROOT), "--evidence", str(FIXTURE),
        "--worker", "recorded", "--session-id", "mock-headless",
    ])
    return repl, runtime


def test_headless_interrupt_ends_the_run(monkeypatch, tmp_path: Path) -> None:
    """A Ctrl+C in a headless run must not be swallowed while piped lines restart the task."""
    def interrupted(line):
        raise KeyboardInterrupt()

    repl, runtime = _headless_runtime(monkeypatch, tmp_path, interrupted, "PROMPT_REVIEW")
    with pytest.raises(KeyboardInterrupt):
        repl.main()
    assert runtime.handled == ["solve it"]


def test_headless_stops_reading_at_waiting_input(monkeypatch, tmp_path: Path) -> None:
    from types import SimpleNamespace

    turn = SimpleNamespace(text="Which file?", closed=False, traces=[])
    repl, runtime = _headless_runtime(monkeypatch, tmp_path, lambda line: turn, "WAITING_INPUT")
    assert repl.main() == 3
    assert runtime.handled == ["solve it"]


def test_sessions_prune_keeps_the_active_session(tmp_path: Path) -> None:
    """The active session's transcript is open: deleting it fails on Windows (and
    crashed the REPL) and silently removed the live session elsewhere."""
    old = tmp_path / "sessions" / "old-session"
    old.mkdir(parents=True)
    os.utime(old, (1_000_000_000, 1_000_000_000))
    proc = _run_repl(tmp_path, ["/sessions prune 0", "/quit"], "active-session")
    out = proc.stdout + proc.stderr
    assert proc.returncode == 0, out[-3000:]
    assert "pruned 1 session(s)" in out
    assert not old.exists()
    assert (tmp_path / "sessions" / "active-session").is_dir()


@pytest.mark.parametrize("name", ["CON", "nul", "com1.log", "Lpt9", "session."])
def test_session_names_reserved_on_windows_are_rejected(name: str) -> None:
    from pdl_taskmaster.host.repl import sanitize_session_name

    with pytest.raises(ValueError):
        sanitize_session_name(name)


def test_ordinary_session_names_are_accepted() -> None:
    from pdl_taskmaster.host.repl import sanitize_session_name

    for name in ("session-20261001-120000", "console", "com10", "my.session"):
        assert sanitize_session_name(name) == name
