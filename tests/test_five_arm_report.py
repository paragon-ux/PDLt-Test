"""The five-route report's arithmetic: the statistics, the pass definition it shares with the scoreboards,
and the dominance rule behind the Pareto table."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments import five_arm_report as report


def test_exact_mcnemar_is_the_two_sided_binomial_tail() -> None:
    assert report.exact_mcnemar(0, 0) == 1.0
    assert report.exact_mcnemar(5, 0) == pytest.approx(0.0625)
    assert report.exact_mcnemar(3, 3) == 1.0
    assert report.exact_mcnemar(1, 7) == pytest.approx(2 * 9 / 256)


def test_wilson_interval_brackets_the_rate_and_stays_in_range() -> None:
    low, high = report.wilson(38, 50)
    assert low < 38 / 50 < high and 0.0 <= low and high <= 1.0
    assert report.wilson(0, 0) == (0.0, 0.0)
    assert report.wilson(10, 10)[1] == pytest.approx(1.0)


def test_dominance_needs_no_worse_everywhere_and_better_somewhere() -> None:
    def arm(rate: float, seconds: float, calls: float) -> dict:
        return {"verified": {"decided_rate": rate}, "latency": {"mean_s": seconds}, "calls": {"per_prompt": calls}}

    dominated = report.pareto({
        "fast_accurate": arm(0.80, 10, 2),
        "slow_accurate": arm(0.80, 30, 5),   # same accuracy, slower and dearer: dominated
        "slow_better": arm(0.90, 30, 5),     # more accurate than the fast one, so the fast one does not dominate it
        "twin": arm(0.80, 10, 2),            # a tie is not domination
    })
    assert dominated["slow_accurate"] == ["fast_accurate", "slow_better", "twin"]
    assert dominated["fast_accurate"] == [] and dominated["twin"] == []
    assert dominated["slow_better"] == []


def _result(pid: str, category: str, *, status: str, grade: str, verdict: str = "CLOSED_SUCCESS",
            seconds: float = 10.0, calls: int = 3) -> dict:
    return {"id": pid, "category": category, "verdict": verdict, "expected_stage": "CLOSED_SUCCESS",
            "ground_truth_status": status, "ground_truth_grade": {"grade": grade, "reason": ""},
            "elapsed_seconds": seconds, "model_calls": {"total": calls}}


def test_a_pass_is_the_expected_stage_and_a_grader_pass_never_an_ungraded_prompt(tmp_path: Path) -> None:
    results = [
        _result("01-01", "combinatorial_search", status="verified", grade="PASS"),
        _result("01-02", "combinatorial_search", status="verified", grade="FAIL"),            # false positive
        _result("01-03", "combinatorial_search", status="verified", grade="MANUAL"),          # pending
        _result("01-04", "combinatorial_search", status="verified", grade="PASS", verdict="TIMEOUT"),  # missed stage
        _result("07-01", "refactoring_and_design", status="not_required", grade="N/A"),       # ungraded
    ]
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    run = {"dir": run_dir, "meta": {"run_id": "run-x", "code": {"commit": "abc", "dirty": False},
                                    "run_settings": {"route": "confirmed"}}, "results": results, "usage": None}
    metrics = report.arm_metrics(run)
    verified = metrics["verified"]
    assert (verified["pass"], verified["fail"], verified["pending"]) == (1, 2, 1)
    assert verified["false_positive"] == 1 and verified["stage_miss"] == 1
    assert verified["decided_rate"] == pytest.approx(1 / 3)
    assert metrics["catalogue"]["ungraded"] == 1 and metrics["catalogue"]["pass"] == 1
    assert metrics["timeouts"] == 1 and metrics["calls"]["total"] == 15


def test_paired_counts_only_the_verified_prompts_both_routes_ran() -> None:
    def run(rows: list[tuple[str, str]]) -> dict:
        return {"results": [_result(pid, "algorithm_design", status="verified", grade=grade) for pid, grade in rows]}

    runs = {
        "unconfirmed": run([("05-01", "PASS"), ("05-02", "PASS"), ("05-03", "FAIL"), ("05-04", "PASS")]),
        "control": run([("05-01", "PASS"), ("05-02", "FAIL"), ("05-03", "PASS")]),
    }
    metrics = {name: report.arm_metrics({"dir": None, "meta": {"run_id": name, "run_settings": {}}, "results": r["results"],
                                         "usage": None}) for name, r in runs.items()}
    (pair,) = [p for p in report.paired(runs, metrics) if (p["a"], p["b"]) == ("unconfirmed", "control")]
    assert (pair["n"], pair["only_a"], pair["only_b"]) == (3, 1, 1)


def test_the_appendix_has_one_row_per_verified_prompt_and_counts_the_routes_that_passed_it() -> None:
    def run(grades: dict[str, str], verdicts: dict[str, str] | None = None) -> dict:
        verdicts = verdicts or {}
        return {"results": [_result(pid, "algorithm_design", status="verified", grade=grade,
                                    verdict=verdicts.get(pid, "CLOSED_SUCCESS")) for pid, grade in grades.items()]}

    runs = {
        "control": run({"05-01": "PASS", "05-02": "FAIL", "05-03": "MANUAL"}),
        "unconfirmed": run({"05-01": "PASS", "05-02": "PASS", "05-03": "PASS"}, {"05-03": "TIMEOUT"}),
    }
    metrics = {name: report.arm_metrics({"dir": None, "meta": {"run_id": name, "run_settings": {}},
                                         "results": value["results"], "usage": None})
               for name, value in runs.items()}
    text = report.appendix(runs, metrics, ["control", "unconfirmed"])
    assert text.startswith("By prompt: 1 prompt passed on 2 routes, 1 prompt passed on 1 route, 1 on no route "
                           "(0 of them awaiting a human check on every route, so not failures).")
    assert "| 05-01 | pass | pass | 2 / 2 |" in text
    assert "| 05-02 | FAIL | pass | 1 / 2 |" in text
    assert "| 05-03 | pending | miss | 0 / 2 |" in text


def test_gate_activity_counts_the_verdicts_and_the_redrafts_they_caused(tmp_path: Path) -> None:
    events = tmp_path / "results" / "01-01" / "session" / "turns" / "events.jsonl"
    events.parent.mkdir(parents=True)
    rows = [
        {"kind": "PROMPT_FIDELITY", "payload": {"verdict": "FAITHFUL"}},
        {"kind": "PROMPT_FIDELITY", "payload": {"verdict": "UNCERTAIN", "fallback": "below_floor"}},
        {"kind": "PROMPT_FIDELITY", "payload": {"verdict": None, "fallback": "sys1_unavailable"}},
        {"kind": "PROMPT_FIDELITY_RETRY", "payload": {}},
        {"kind": "PLAN_ADVANCEMENT", "payload": {"verdict": "RESTATES"}},
        {"kind": "PLAN_ADVANCEMENT_RETRY", "payload": {}},
        {"kind": "TURN_STATUS", "payload": {}},
    ]
    events.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    gates = report.gate_activity(tmp_path)
    assert gates["fidelity"] == {"FAITHFUL": 1, "UNCERTAIN": 1, "NO_DECISION": 1}
    assert gates["advancement"] == {"RESTATES": 1}
    assert gates["events"] == {"PROMPT_FIDELITY_RETRY": 1, "PLAN_ADVANCEMENT_RETRY": 1}
    assert report.gate_activity(None) == {}


def test_brief_split_separates_the_prompts_where_the_brief_ran_from_the_noise_elsewhere() -> None:
    def result(pid: str, grade: str, brief: bool = False) -> dict:
        row = _result(pid, "combinatorial_search", status="verified", grade=grade)
        row["model_calls"] = {"total": 3, "by_operation": {"DRAFT_EXECUTE": 1} if brief else {}}
        return row

    plain = {"results": [result("01-01", "PASS"), result("05-01", "PASS"), result("05-02", "FAIL"), result("05-03", "PASS")]}
    brief = {"results": [result("01-01", "FAIL", brief=True), result("05-01", "PASS"), result("05-02", "PASS"),
                         result("05-03", "FAIL")]}
    runs = {"unconfirmed": plain, "unconfirmed-draft-execute": brief}
    metrics = {name: report.arm_metrics({"dir": None, "meta": {"run_id": name, "run_settings": {}},
                                         "results": value["results"], "usage": None}) for name, value in runs.items()}
    (row,) = report.brief_split(runs, metrics)
    assert row["ran_on"] == ["01-01"]
    assert (row["with_brief"]["n"], row["with_brief"]["plain"], row["with_brief"]["brief"]) == (1, 1, 0)
    assert (row["without_brief"]["n"], row["without_brief"]["only_plain"], row["without_brief"]["only_brief"]) == (3, 1, 1)
    assert row["without_brief"]["p"] == 1.0


def _run(results: list[dict], **extra) -> dict:
    return {"dir": None, "meta": {"run_id": "run-x", "run_settings": {}}, "results": results, "usage": None, **extra}


def test_regraded_grades_replace_only_those_that_changed_and_are_listed_next_to_the_recorded_ones() -> None:
    results = [
        _result("01-01", "combinatorial_search", status="verified", grade="PASS"),
        _result("01-02", "combinatorial_search", status="verified", grade="FAIL"),
        _result("01-03", "combinatorial_search", status="verified", grade="FAIL"),
        _result("07-01", "refactoring_and_design", status="not_required", grade="N/A"),
    ]
    run = _run(results)
    grades = {
        "01-01": {"old": "PASS", "new": "PASS", "reason": "ok"},
        "01-02": {"old": "FAIL", "new": "PASS", "reason": "now readable"},
        "01-03": {"old": "FAIL", "new": "FAIL", "reason": "wrong"},
        "07-01": {"old": "N/A", "new": "N/A", "reason": ""},
    }
    after = report.with_grades(run, grades)
    assert report.arm_metrics(run, light=True)["verified"]["pass"] == 1
    assert report.arm_metrics(after, light=True)["verified"]["pass"] == 2
    assert run["results"][1]["ground_truth_grade"]["grade"] == "FAIL"  # the recorded run itself is not touched
    assert report.grade_changes({"confirmed": run}, {"confirmed": grades}) == [
        {"route": "confirmed", "id": "01-02", "old": "FAIL", "new": "PASS", "reason": "now readable"}]


def test_token_totals_sum_every_call_of_every_result(tmp_path: Path) -> None:
    dirs = []
    for index in range(2):
        folder = tmp_path / f"r{index}"
        (folder / "session" / "observations").mkdir(parents=True)
        record = {"calls": [
            {"operation": "BOOTSTRAP_ANALYSIS", "usage": {"input_tokens": 100, "output_tokens": 10, "reasoning_tokens": 0,
                                                          "cached_tokens": 40}},
            {"operation": "EXECUTE_UNCONFIRMED", "usage": {"input_tokens": 300, "output_tokens": 50, "reasoning_tokens": 0,
                                                            "cached_tokens": 100}},
        ]}
        (folder / "session" / "observations" / "repl-session.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
        dirs.append(folder)
    assert report.token_totals({"result_dirs": dirs}) == {"input": 800, "cached": 280, "output": 120}
    assert report.token_totals({}) == {"input": 0, "cached": 0, "output": 0}


def test_gate_activity_counts_how_the_computation_question_was_answered(tmp_path: Path) -> None:
    rows = [
        {"kind": "COMPUTATION_CLASSIFIED", "payload": {"computational": True, "fallback": None}},
        {"kind": "COMPUTATION_CLASSIFIED", "payload": {"computational": False, "fallback": "below_floor"}},
        {"kind": "COMPUTATION_CLASSIFIED", "payload": {"computational": False, "fallback": None}},
    ]
    (tmp_path / "events.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    assert report.gate_activity(tmp_path)["computation"] == {"yes": 1, "below_floor": 1, "no": 1}


def test_the_report_shows_the_regrade_and_the_tokens_next_to_the_recorded_numbers() -> None:
    plain = _run([_result("01-01", "combinatorial_search", status="verified", grade="FAIL")])
    control = _run([_result("01-01", "combinatorial_search", status="verified", grade="FAIL")])
    runs = {"control": control, "unconfirmed": plain}
    grades = {"control": {"01-01": {"old": "FAIL", "new": "PASS", "reason": "valid coloring"}},
              "unconfirmed": {"01-01": {"old": "FAIL", "new": "FAIL", "reason": "wrong"}}}
    recorded = {n: report.arm_metrics(run, light=True) for n, run in runs.items()}
    regraded = {n: report.with_grades(run, grades[n]) for n, run in runs.items()}
    metrics = {n: report.arm_metrics(run) for n, run in regraded.items()}

    def render(**extra) -> str:
        return report.render(regraded, metrics, report.by_category(regraded, metrics), report.paired(regraded, metrics),
                             report.pareto(metrics), report.brief_split(regraded, metrics), **extra)

    markdown = render(recorded=recorded, changes=report.grade_changes(runs, grades))
    assert "after the grader fixes" in markdown
    assert "| Control: direct model | 0 / 1 = 0.0% | 1 / 1 = 100.0% | 1 |" in markdown  # as recorded, then with today's graders
    assert "| Control | 01-01 | FAIL | PASS | valid coloring |" in markdown
    assert "Tokens in / cached / out (M)" in markdown
    assert "after the grader fixes" not in render()  # without --regrade there is nothing to set beside


def test_the_appendix_does_not_count_a_prompt_awaiting_a_human_check_as_a_failure() -> None:
    def results(rows: list[tuple[str, str]]) -> list[dict]:
        return [_result(pid, "formal_verification", status="verified", grade=grade) for pid, grade in rows]

    runs = {"control": _run(results([("14-02", "MANUAL"), ("04-02", "FAIL"), ("01-01", "PASS")])),
            "unconfirmed": _run(results([("14-02", "MANUAL"), ("04-02", "FAIL"), ("01-01", "FAIL")]))}
    metrics = {name: report.arm_metrics(run) for name, run in runs.items()}
    text = report.appendix(runs, metrics, ["control", "unconfirmed"])
    assert "1 prompt passed on 1 route" in text
    assert "2 on no route (1 of them awaiting a human check on every route, so not failures)" in text
