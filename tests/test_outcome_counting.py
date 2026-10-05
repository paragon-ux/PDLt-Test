"""An ungraded result is never a pass, and a hold has its own count
(TARGET_ARCHITECTURE I-11; LEDGER L49d; decision D3; GOAL T0.7)."""
from __future__ import annotations

import json
from pathlib import Path

import graders
import run_catalogue


def _result(pid: str, verdict: str, grade: str, category: str = "logic_and_reasoning") -> dict:
    return {"id": pid, "category": category, "difficulty": "easy", "verdict": verdict,
            "expected_stage": "CLOSED_SUCCESS", "elapsed_seconds": 1.0,
            "ground_truth_grade": {"grade": grade}, "regression_ref": None}


UNGRADED = _result("08-01", "CLOSED_SUCCESS", graders.NA)
PASSED = _result("16-06", "CLOSED_SUCCESS", graders.PASS)
FAILED = _result("16-03", "CLOSED_SUCCESS", graders.FAIL)
PENDING = _result("16-01", "CLOSED_SUCCESS", graders.MANUAL)
HELD = _result("12-01", run_catalogue.HOLD_VERDICT, graders.NA)
HELD_ADVERSARIAL = _result("09-01", run_catalogue.HOLD_VERDICT, graders.NA, "adversarial_and_injection")


def test_each_result_has_exactly_one_outcome() -> None:
    assert [run_catalogue.outcome_class(r) for r in (PASSED, FAILED, PENDING, UNGRADED, HELD)] == [
        "PASS", "FAIL", "PENDING", "UNGRADED", "HELD"]


def test_an_ungraded_result_is_counted_as_ungraded_not_passed() -> None:
    assert not run_catalogue.is_prompt_pass(UNGRADED)
    assert run_catalogue.is_prompt_ungraded(UNGRADED)
    assert run_catalogue.is_prompt_pass_legacy(UNGRADED)  # what the old counting did


def test_a_hold_is_never_a_pass_and_has_its_own_count() -> None:
    assert run_catalogue.is_prompt_held(HELD) and not run_catalogue.is_prompt_pass(HELD)
    assert not run_catalogue.is_prompt_fail(HELD)


def test_fail_fast_stops_on_a_false_hold_but_not_on_an_adversarial_hold() -> None:
    assert run_catalogue.stops_fail_fast(FAILED)
    assert run_catalogue.stops_fail_fast(HELD)
    assert not run_catalogue.stops_fail_fast(HELD_ADVERSARIAL)
    assert not run_catalogue.stops_fail_fast(UNGRADED)


def test_the_scoreboard_reports_both_countings_side_by_side(tmp_path: Path) -> None:
    results = [PASSED, FAILED, PENDING, UNGRADED, HELD]
    meta = {"run_id": "run-test", "start_time": "t", "model": "m", "reasoning_effort": "low"}
    run_catalogue.generate_scoreboard(results, tmp_path, meta)
    board = json.loads((tmp_path / "SCOREBOARD.json").read_text(encoding="utf-8"))
    assert (board["passed"], board["failed"], board["pending_human_check"], board["ungraded"], board["held"]) == (
        1, 1, 1, 1, 1)
    assert board["legacy_passed"] == 2  # PASS + the ungraded result, as before L49d
    assert board["pass_rate_pct"] == 20.0 and board["legacy_pass_rate_pct"] == 40.0
    markdown = (tmp_path / "SCOREBOARD.md").read_text(encoding="utf-8")
    assert "Ungraded" in markdown and "old counting" in markdown


def test_counts_feed_the_arm_reports_with_old_and_new_counting() -> None:
    counts = run_catalogue.outcome_counts([PASSED, UNGRADED, UNGRADED, HELD])
    assert (counts["pass"], counts["ungraded"], counts["held"], counts["legacy_pass"]) == (1, 2, 1, 3)
    assert run_catalogue.format_counts(counts).startswith("pass 1/4 (old counting 3/4)")


def test_the_four_arm_report_counts_from_results_not_from_old_scoreboards(tmp_path: Path, monkeypatch, capsys) -> None:
    import experiments.run_four_arms as four

    run = tmp_path / "catalogue-runs" / "run-20261005-000000-confirmed"
    (run / "results").mkdir(parents=True)
    # An old scoreboard that counted the ungraded prompt as a pass.
    (run / "SCOREBOARD.json").write_text(json.dumps({"total_prompts": 2, "passed": 2, "pass_rate_pct": 100.0}),
                                         encoding="utf-8")
    for r in (PASSED, UNGRADED):
        (run / "results" / r["id"]).mkdir()
        (run / "results" / r["id"] / "result.json").write_text(json.dumps(r), encoding="utf-8")
    monkeypatch.setattr(four, "ROOT", tmp_path)
    four.summarize_results("16-06,08-01")
    out = capsys.readouterr().out
    assert "pass 1/2 (old counting 2/2)" in out and "ungraded 1" in out
