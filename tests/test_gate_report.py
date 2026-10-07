"""The live-gate report (GOAL T0.7b): outcome classes, the 09-xx reading from the run
record, cost from recorded usage, and comparisons with n and a Wilson interval."""
from __future__ import annotations

import json
from pathlib import Path

import graders
from experiments import gate_report


def _prompt(run: Path, name: str, category: str, verdict: str, grade: str, *, bootstrap_kind: str | None = None,
            disposition: str | None = None, tokens: tuple[int, int] = (1000, 200)) -> None:
    folder = run / "results" / name
    session = folder / "session" / "W-1" / "turns" / "turn_001"
    (session / "events").mkdir(parents=True)
    (folder / "result.json").write_text(json.dumps({
        "id": name[:5], "category": category, "verdict": verdict, "expected_stage": "CLOSED_SUCCESS",
        "ground_truth_grade": {"grade": grade}}), encoding="utf-8")
    events = [{"event": gate_report.DISPOSITION_EVENT, "payload": {"disposition": disposition}}] if disposition else []
    (session / "events" / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
    if bootstrap_kind:
        reply = session / "stages" / "10_prompt" / "output" / "0001-bootstrap_analysis"
        reply.mkdir(parents=True)
        (reply / "model-response.txt").write_text(json.dumps({"kind": bootstrap_kind}), encoding="utf-8")
    observations = folder / "session" / "s" / "observations"
    observations.mkdir(parents=True)
    (observations / "repl-session.jsonl").write_text(json.dumps(
        {"calls": [{"usage": {"input_tokens": tokens[0], "output_tokens": tokens[1]}}]}), encoding="utf-8")


def test_wilson_interval() -> None:
    low, high = gate_report.wilson(1, 5)
    assert round(low, 3) == 0.036 and round(high, 3) == 0.624
    assert gate_report.wilson(0, 0) == (0.0, 1.0)


def test_the_09_outcome_is_read_from_the_run_record(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _prompt(run, "09-01_a", "adversarial_and_injection", "CLOSED_SUCCESS", graders.NA,
            bootstrap_kind="BLOCKED_BY_HIGHER_PRIORITY")
    _prompt(run, "09-01_b", "adversarial_and_injection", "CLOSED_SUCCESS", graders.NA, disposition="CONTAIN")
    _prompt(run, "09-01_c", "adversarial_and_injection", "UNCONFIRMED_GATE", graders.NA)
    _prompt(run, "09-01_d", "adversarial_and_injection", "CLOSED_SUCCESS", graders.NA, bootstrap_kind="ANALYSIS")
    readings = {r["dir"]: r["adversarial"] for r in gate_report.read_run(run)}
    assert readings == {"09-01_a": "blocked", "09-01_b": "contained", "09-01_c": "held", "09-01_d": "proceeded"}


def test_counts_cost_and_old_counting(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _prompt(run, "16-06_a", "logic_and_reasoning", "CLOSED_SUCCESS", graders.PASS)
    _prompt(run, "08-01_a", "specification_extraction", "CLOSED_SUCCESS", graders.NA)
    rows = gate_report.read_run(run)
    summary = gate_report.summary(rows)
    assert (summary["pass"], summary["ungraded"], summary["legacy_pass"], summary["total"]) == (1, 1, 2, 2)
    assert summary["cost"] == round(2 * (1000 / 1e6 * 0.05 + 200 / 1e6 * 0.25), 4)
    assert "old counting 2/2" in gate_report.render(run, rows)


def test_a_comparison_whose_intervals_overlap_is_anecdotal() -> None:
    small = {"pass": 1, "total": 5, "pass_interval": gate_report.wilson(1, 5)}
    same = {"pass": 2, "total": 5, "pass_interval": gate_report.wilson(2, 5)}
    assert gate_report.compare(small, same).endswith("anecdotal (the intervals overlap)")
    high = {"pass": 50, "total": 50, "pass_interval": gate_report.wilson(50, 50)}
    low = {"pass": 0, "total": 50, "pass_interval": gate_report.wilson(0, 50)}
    assert gate_report.compare(high, low).endswith("intervals separate the runs")
