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
