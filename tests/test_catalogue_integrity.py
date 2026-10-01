"""Evaluation plane: prompts are exactly what a user would send.

Evaluator guidance (expected behaviour, multi-turn scripts) lives in the manifest,
which the runner never passes to the harness. Text addressed to a tester inside a
prompt would tell the model how it is being graded.
"""
from __future__ import annotations

import json
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
    code, timed_out = run_catalogue.run_with_deadline(
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

    code, timed_out = run_catalogue.run_with_deadline(
        [sys.executable, "-c", "import sys; print(sys.stdin.read().strip()); sys.exit(3)"], "hello", 30,
        tmp_path / "out.txt", tmp_path / "err.txt",
    )
    assert (code, timed_out) == (3, False) and (tmp_path / "out.txt").read_text().strip() == "hello"
