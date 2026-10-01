"""Evaluation plane: prompts are exactly what a user would send.

Evaluator guidance (expected behaviour, multi-turn scripts) lives in the manifest,
which the runner never passes to the harness. Text addressed to a tester inside a
prompt would tell the model how it is being graded.
"""
from __future__ import annotations

import json
import time
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "prompts"

_TESTER_FACING = re.compile(
    r"note\s+to\s+tester|\btester\b|expected\s+behaviou?r|multi-turn\s+test|designed\s+for\s+multi-turn",
    re.IGNORECASE,
)


def _manifest() -> list[dict]:
    text = (PROMPTS / "CATALOGUE_MANIFEST.jsonl").read_text(encoding="utf-8-sig")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def test_prompts_contain_no_tester_facing_text():
    offenders = []
    for entry in _manifest():
        text = (PROMPTS / entry["file"]).read_text(encoding="utf-8-sig")
        match = _TESTER_FACING.search(text)
        if match:
            offenders.append(f"{entry['id']}: {match.group(0)!r}")
    assert not offenders, "tester-facing text inside prompts:\n" + "\n".join(offenders)


def test_evaluator_notes_live_in_the_manifest():
    entries = {e["id"]: e for e in _manifest()}
    noted = {i for i, e in entries.items() if e.get("tester_note")}
    scripted = {i for i, e in entries.items() if e.get("multi_turn_script")}
    assert {"13-02", "13-03", "13-04", "13-05", "13-06", "13-07", "14-07"} <= noted
    assert scripted == {i for i in entries if i.startswith("10-")}


def test_runner_sends_only_the_prompt_file():
    """The harness receives --prompt-file; manifest fields never reach its command line or stdin."""
    runner = (ROOT / "run_catalogue.py").read_text(encoding="utf-8")
    command = runner.split("cmd = [", 1)[1].split("]", 1)[0]
    assert "tester_note" not in command and "multi_turn_script" not in command
    assert '"--prompt-file", str(prompt_file)' in command
    assert 'repl_input = "/confirm\\n" * 5' in runner


def test_repeat_runs_report_a_pass_rate_per_prompt(tmp_path):
    import sys

    sys.path.insert(0, str(ROOT))
    import run_catalogue

    def result(pid, verdict, k):
        return {"id": pid, "category": "c", "difficulty": "d", "verdict": verdict, "expected_stage": "CLOSED_SUCCESS",
                "elapsed_seconds": 1.0, "ground_truth_grade": {"grade": "N/A"}, "model_calls": {}, "repeat": k,
                "regression_ref": None}

    results = [result("01-01", v, k) for k, v in enumerate(["CLOSED_SUCCESS", "CLOSED_CANCELLED", "CLOSED_SUCCESS"], 1)]
    meta = {"run_id": "r", "start_time": "t", "model": "m", "reasoning_effort": "low"}
    scoreboard = run_catalogue.generate_scoreboard(results, tmp_path, meta)
    assert scoreboard["repeat_pass_rates"] == {"01-01": {"runs": 3, "passed": 2}}
    assert "| 01-01 | 2 | 3 |" in (tmp_path / "SCOREBOARD.md").read_text(encoding="utf-8")


def test_hung_prompt_is_killed_with_its_whole_process_tree(tmp_path):
    """EXECUTE=high runs (2026-10-01) appeared to hang: the runner must return at
    its deadline even when a grandchild still holds the output handles."""
    import subprocess
    import sys
    import time

    sys.path.insert(0, str(ROOT))
    import run_catalogue

    pid_file = tmp_path / "grandchild.pid"
    child = (
        "import subprocess, sys, time\n"
        f"g = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])\n"
        f"open({str(pid_file)!r}, 'w').write(str(g.pid))\n"
        "print('started', flush=True)\n"
        "time.sleep(120)\n"
    )
    started = time.monotonic()
    code, timed_out, _ = run_catalogue.run_with_deadline(
        [sys.executable, "-c", child], "", 3, tmp_path / "out.txt", tmp_path / "err.txt"
    )
    assert timed_out and code == -1
    assert time.monotonic() - started < 20
    assert "started" in (tmp_path / "out.txt").read_text()  # progress is on disk, not lost in a pipe
    grandchild = int(pid_file.read_text())
    time.sleep(0.5)
    if sys.platform != "win32":
        import os

        try:
            os.kill(grandchild, 0)
            alive = subprocess.run(["ps", "-o", "stat=", "-p", str(grandchild)], capture_output=True,
                                   text=True).stdout.strip()
            assert alive.startswith("Z") or not alive  # reaped or zombie, not running
        except ProcessLookupError:
            pass


def test_prompt_within_its_deadline_returns_its_exit_code(tmp_path):
    import sys

    sys.path.insert(0, str(ROOT))
    import run_catalogue

    code, timed_out, _ = run_catalogue.run_with_deadline(
        [sys.executable, "-c", "import sys; print(sys.stdin.read().strip()); sys.exit(3)"], "hello", 30,
        tmp_path / "out.txt", tmp_path / "err.txt",
    )
    assert (code, timed_out) == (3, False) and (tmp_path / "out.txt").read_text().strip() == "hello"


def test_harness_peak_memory_is_measured(tmp_path):
    import sys

    sys.path.insert(0, str(ROOT))
    import run_catalogue

    code, timed_out, containment = run_catalogue.run_with_deadline(
        [sys.executable, "-c", "x = bytearray(80 * 1024 * 1024); x[::4096] = b'1' * len(x[::4096])"], "", 30,
        tmp_path / "out.txt", tmp_path / "err.txt",
    )
    assert (code, timed_out) == (0, False)
    assert containment.peak_mb is not None and containment.peak_mb >= 80
    assert not containment.limit_reached


def test_harness_over_its_memory_cap_is_a_harness_fault_not_a_model_outcome(tmp_path):
    """Run 20261001-154533 froze the evaluator's machine at 80% memory; one prompt's
    harness tree is now capped, and exceeding the cap is reported as such."""
    import sys

    sys.path.insert(0, str(ROOT))
    import run_catalogue

    started = time.monotonic()
    code, timed_out, containment = run_catalogue.run_with_deadline(
        [sys.executable, "-c", "x = [bytearray(64 * 1024 * 1024) for _ in range(64)]"], "", 60,
        tmp_path / "out.txt", tmp_path / "err.txt", memory_mb=512,
    )
    stderr = (tmp_path / "err.txt").read_text()
    assert code != 0 and not timed_out and time.monotonic() - started < 30
    assert run_catalogue.harness_fault(containment, stderr) == "HARNESS_MEMORY_LIMIT"


def test_harness_that_hangs_after_its_session_dumps_stacks_and_exits(tmp_path):
    """The exit watchdog (host/cli.py): a process that does not exit after the
    session ended dumps every thread's stack and exits; the runner reports
    HARNESS_HANG instead of waiting out the prompt deadline."""
    import sys

    sys.path.insert(0, str(ROOT))
    import run_catalogue

    child = (
        "import sys, threading\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "from pdl_taskmaster.host.cli import _arm_exit_watchdog\n"
        "threading.Thread(target=threading.Event().wait).start()  # never ends: shutdown hangs\n"
        "_arm_exit_watchdog(1)\n"
    )
    started = time.monotonic()
    code, timed_out, containment = run_catalogue.run_with_deadline(
        [sys.executable, "-c", child], "", 60, tmp_path / "out.txt", tmp_path / "err.txt",
    )
    stderr = (tmp_path / "err.txt").read_text()
    assert not timed_out and time.monotonic() - started < 15
    assert run_catalogue.harness_fault(containment, stderr) == "HARNESS_HANG"
    assert "threading.py" in stderr  # the dump names where it hung


def test_clean_exit_after_the_watchdog_is_armed_leaves_no_trace(tmp_path):
    import sys

    sys.path.insert(0, str(ROOT))
    import run_catalogue

    child = (
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "from pdl_taskmaster.host.cli import _arm_exit_watchdog\n"
        "_arm_exit_watchdog(5)\n"
    )
    code, timed_out, containment = run_catalogue.run_with_deadline(
        [sys.executable, "-c", child], "", 60, tmp_path / "out.txt", tmp_path / "err.txt",
    )
    assert (code, timed_out) == (0, False) and (tmp_path / "err.txt").read_text() == ""
    assert run_catalogue.harness_fault(containment, "") is None
