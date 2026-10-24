"""L143: experiments/tool_attribution.py reads paired runs from their own records, counts what it says it counts, and
makes missing or malformed records visible (exit 1 unless --allow-missing). Synthetic run folders; offline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments import tool_attribution as ta


def _call(tool, attempt=1, accepted=None, codes=()):
    payload = {"n": 1, "attempt": attempt, "tool": tool}
    if accepted is not None:
        payload["accepted"] = accepted
        payload["envelope"] = {"ok": accepted, "errors": [{"code": c} for c in codes], "facts": []}
    return {"at_utc": f"2026-10-18T00:00:{attempt:02d}+00:00", "kind": "AGENT_TOOL_CALL", "payload": payload}


def _run(root: Path, name: str, rows: list[dict], *, agent_tools=False) -> Path:
    run = root / name
    (run / "results").mkdir(parents=True)
    (run / "RUN_META.json").write_text(json.dumps({
        "route": "unconfirmed", "repeat": 2, "reasoning_effort": "low", "prompt_id_filter": "01-01,02-01",
        "run_settings": {"agent_tools": agent_tools, "providers": "P"}, "code": {"commit": "abcdef12", "dirty": False}}),
        encoding="utf-8")
    for row in rows:
        folder = run / "results" / f"{row['id']}_x_r{row['repeat']}"
        session = folder / "session" / "W-1" / "turns" / "turn_001"
        (session / "events").mkdir(parents=True)
        if row.get("result", True):
            (folder / "result.json").write_text(json.dumps({
                "id": row["id"], "repeat": row["repeat"], "verdict": row["verdict"], "expected_stage": "CLOSED_SUCCESS",
                "ground_truth_grade": {"grade": row["grade"]}}), encoding="utf-8")
        lines = [json.dumps(e) for e in row.get("events", [])] + row.get("raw_lines", [])
        (session / "events" / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        if row.get("level"):
            output = session / "stages" / "50_execution" / "output"
            output.mkdir(parents=True)
            (output / "provenance.json").write_text(json.dumps({"verification": {"level": row["level"]}}),
                                                    encoding="utf-8")
    return run


@pytest.fixture
def arms(tmp_path):
    reference = _run(tmp_path, "run-a", [
        {"id": "01-01", "repeat": 1, "verdict": "CLOSED_SUCCESS", "grade": "PASS", "level": "host_verified"},
        {"id": "01-01", "repeat": 2, "verdict": "CLOSED_SUCCESS", "grade": "FAIL", "level": "contract_checked"},
        {"id": "02-01", "repeat": 1, "verdict": "CLOSED_SUCCESS", "grade": "PASS", "level": "contract_checked"},
        {"id": "02-01", "repeat": 2, "verdict": "CLOSED_SUCCESS", "grade": "MANUAL", "level": "contract_checked"},
    ])
    tools = _run(tmp_path, "run-b", [
        {"id": "01-01", "repeat": 1, "verdict": "CLOSED_SUCCESS", "grade": "FAIL", "level": "host_verified",
         "events": [_call("submit_bootstrap_analysis", accepted=True), _call("run_python"), _call("run_python"),
                    _call("submit_execute_unconfirmed", accepted=False, codes=("NO_PROGRAM",)),
                    _call("submit_execute_unconfirmed", attempt=2, accepted=True)]},
        {"id": "01-01", "repeat": 2, "verdict": "CLOSED_SUCCESS", "grade": "PASS", "level": "host_verified",
         "events": [_call("submit_execute_unconfirmed", accepted=True)]},
        {"id": "02-01", "repeat": 1, "verdict": "CLOSED_CANCELLED", "grade": "FAIL"},
        {"id": "02-01", "repeat": 2, "verdict": "CLOSED_SUCCESS", "grade": "PASS", "level": "contract_checked"},
    ], agent_tools=True)
    return tmp_path, reference, tools


def test_outcomes_tools_and_false_positives_are_counted_from_the_records(arms):
    _, reference, tools = arms
    problems: list[str] = []
    a, b = ta.load_run(reference, problems), ta.load_run(tools, problems)
    assert problems == []
    sa, sb = ta.arm_summary(a), ta.arm_summary(b)
    assert (sa["grades"]["PASS"], sa["grades"]["FAIL"], sa["grades"]["MANUAL"], sa["decided"]) == (2, 1, 1, 3)
    assert sa["false_positives"] == ["01-01 r2"] and sb["false_positives"] == ["01-01 r1"]
    assert sb["tools"]["run_python"] == {"calls": 2, "runs": 1}
    assert sb["tools"]["submit_execute_unconfirmed"] == {"calls": 3, "runs": 2, "accepted": 2, "rejected": 1}
    assert sb["rejection_codes"] == {"NO_PROGRAM": 1}
    assert sa["levels"] == {"host_verified": 1, "contract_checked": 3} and sb["levels"][None] == 1


def test_paired_tests_count_discordant_runs_and_prompts(arms):
    _, reference, tools = arms
    problems: list[str] = []
    p = ta.paired(ta.load_run(reference, problems), ta.load_run(tools, problems), problems)
    # Passes: reference 01-01 r1, 02-01 r1; other 01-01 r2, 02-01 r2 (MANUAL counts as not passed).
    assert (p["passes"]["only_a"], p["passes"]["only_b"], p["passes"]["n"]) == (2, 2, 4)
    assert p["decided"]["n"] == 3  # 02-01 r2 is MANUAL in the reference
    assert (p["wins"], p["losses"], p["ties"]) == (0, 0, 2) and p["sign_p"] == 1.0
    assert p["false_positives"]["only_a"] == 1 and p["false_positives"]["only_b"] == 1


def test_the_report_states_its_inputs_and_rules_and_runs_end_to_end(arms, tmp_path):
    root, reference, tools = arms
    out = tmp_path / "report.md"
    assert ta.main([str(reference), str(tools), "--md", str(out), "--trace", "01-01:1"]) == 0
    text = out.read_text(encoding="utf-8")
    for expected in ("| `run-a` | `abcdef12` | clean | unconfirmed | False | low | P |", "Script commit:",
                     "2/3 (66.7%)", "| `run-b` | `submit_execute_unconfirmed` | 3 | 2 of 4 | 2 | 1 |",
                     "attempt 1: submit_execute_unconfirmed rejected (NO_PROGRAM)", "## Data problems\n\nNone.",
                     "Correlation and causation"):
        assert expected in text, expected


def test_missing_or_malformed_records_are_listed_and_fail_the_run(tmp_path):
    reference = _run(tmp_path, "run-a", [
        {"id": "01-01", "repeat": 1, "verdict": "CLOSED_SUCCESS", "grade": "PASS"},
        {"id": "01-01", "repeat": 2, "verdict": "CLOSED_SUCCESS", "grade": "PASS", "result": False},
    ])
    tools = _run(tmp_path, "run-b", [
        {"id": "01-01", "repeat": 1, "verdict": "CLOSED_SUCCESS", "grade": "PASS", "raw_lines": ["{not json"]},
    ], agent_tools=True)
    out = tmp_path / "report.md"
    assert ta.main([str(reference), str(tools), "--md", str(out)]) == 1
    text = out.read_text(encoding="utf-8")
    assert "run-a/01-01_x_r2: result.json missing or unreadable" in text
    assert "run-b/01-01_x_r1: events.jsonl line 1 is not JSON" in text
    assert ta.main([str(reference), str(tools), "--md", str(out), "--allow-missing"]) == 0


def test_an_unpaired_run_is_a_data_problem(tmp_path):
    reference = _run(tmp_path, "run-a", [{"id": "01-01", "repeat": 1, "verdict": "CLOSED_SUCCESS", "grade": "PASS"},
                                         {"id": "01-01", "repeat": 2, "verdict": "CLOSED_SUCCESS", "grade": "PASS"}])
    other = _run(tmp_path, "run-b", [{"id": "01-01", "repeat": 1, "verdict": "CLOSED_SUCCESS", "grade": "PASS"}])
    problems: list[str] = []
    ta.paired(ta.load_run(reference, problems), ta.load_run(other, problems), problems)
    assert problems == ["01-01 r2 is not in both run-a and run-b"]
