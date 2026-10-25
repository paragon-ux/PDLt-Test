"""F7: scripted child processes prove discovery, resume identity and complete coverage. Offline."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments import premerge_catalogue as check

CODE = {"commit": "abc123", "dirty": False, "diff_sha256": None}
IDS = ["01-01", "01-02"]


def _result(pid, verdict="CLOSED_UNVERIFIED"):
    return {"id": pid, "category": "one", "verdict": verdict, "expected_stage": "CLOSED_UNVERIFIED",
            "ground_truth_grade": {"grade": "PASS"}}


def _run(folder, rows, **metadata):
    for index, row in enumerate(rows):
        path = folder / "results" / str(index) / "result.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(row), encoding="utf-8")
    (folder / "results").mkdir(parents=True, exist_ok=True)
    meta = {"run_id": folder.name, "code": CODE, "model": check.MODEL, "route": "unconfirmed", "repeat": 1,
            "manifest": None, "category_filter": "one", "prompt_id_filter": None, "run_settings": {}}
    (folder / "RUN_META.json").write_text(json.dumps({**meta, **metadata}), encoding="utf-8")
    (folder / "SCOREBOARD.json").write_text(json.dumps({"total_prompts": len(rows)}), encoding="utf-8")


@pytest.fixture
def driver(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "prompts").mkdir(parents=True)
    (repo / "prompts" / "CATALOGUE_MANIFEST.jsonl").write_text(
        "".join(json.dumps({"id": pid, "category": "one"}) + "\n" for pid in IDS), encoding="utf-8")
    archive = tmp_path / "configured"
    baseline = archive / "baseline"
    _run(baseline, [_result(pid) for pid in IDS])
    monkeypatch.setenv("PDLT_CATALOGUE_RUNS", "../configured")
    monkeypatch.setattr(check.run_catalogue, "code_provenance", lambda root: CODE)
    monkeypatch.setattr(check.matched_study, "key_state", lambda: {"limit_remaining": 1.0})
    return check.CatalogueCheck(repo, tmp_path / "state.json", baseline)


def _child(monkeypatch, responses):
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        action = responses[len(calls) - 1]
        root = Path(kwargs["env"]["PDLT_CATALOGUE_RUNS"])
        assert root.is_absolute() and "configured" in root.parts
        return SimpleNamespace(returncode=action(root, command))

    monkeypatch.setattr(check.subprocess, "run", run)
    return calls


def test_partial_fail_fast_then_single_prompt_proves_exact_coverage(driver, monkeypatch):
    def partial(root, command):
        _run(root / "run-first", [_result(IDS[0], "CLOSED_CANCELLED")])
        return 1

    def rest(root, command):
        assert command[-2:] == ["--prompt-id", IDS[1]]
        _run(root / "run-second", [_result(IDS[1])], category_filter=None, prompt_id_filter=IDS[1])
        return 0

    calls = _child(monkeypatch, [partial, rest])
    summary = driver.run()
    assert summary["prompts"] == 2 and summary["counts"] == {"FAIL": 1, "PASS": 1}
    assert len(calls) == 2 and summary["regressions"] == [IDS[0]]
    resumed = check.CatalogueCheck(driver.repo, driver.out, driver.archive / "baseline")
    assert resumed.run() == summary and len(calls) == 2


@pytest.mark.parametrize("problem", ["missing", "ambiguous", "empty", "unexpected", "duplicate", "malformed",
                                     "partial_without_stop", "harness", "bad_exit", "foreign", "wrong_filter",
                                     "unexplained_exit"])
def test_invalid_child_output_never_becomes_coverage(driver, monkeypatch, problem):
    def bad(root, command):
        if problem == "missing":
            return 0
        rows = [_result(pid) for pid in IDS]
        if problem == "empty":
            rows = []
        if problem == "unexpected":
            rows = [_result("foreign")]
        if problem == "duplicate":
            rows = [_result(IDS[0]), _result(IDS[0])]
        if problem == "partial_without_stop":
            rows = [_result(IDS[0])]
        if problem == "harness":
            rows = [_result(IDS[0], "HARNESS_ERROR")]
        folder = root / "run-test"
        metadata = {"code": {**CODE, "commit": "wrong"}} if problem == "foreign" else {}
        if problem == "wrong_filter":
            metadata["category_filter"] = "other"
        _run(folder, rows, **metadata)
        if problem == "ambiguous":
            _run(root / "run-another", rows)
        if problem == "malformed":
            (folder / "results" / "0" / "result.json").write_text("{", encoding="utf-8")
        return 4 if problem == "bad_exit" else 1 if problem == "unexplained_exit" else 0

    _child(monkeypatch, [bad])
    with pytest.raises(ValueError, match="invalid child output"):
        driver.run()
    assert not driver.state["outcomes"] and "summary" not in driver.state
    assert driver.state["runs"][-1]["error"]


def test_resume_validates_saved_evidence_before_budget_or_child_calls(driver, monkeypatch):
    def partial(root, command):
        _run(root / "run-first", [_result(IDS[0], "CLOSED_CANCELLED")])
        return 1

    _child(monkeypatch, [partial])
    driver.invoke(["--category", "one"], IDS)
    record = driver.state["outcomes"][IDS[0]]
    (driver.archive / record["run"] / "results" / "0" / "result.json").unlink()
    monkeypatch.setattr(check.matched_study, "key_state", lambda: pytest.fail("no paid/budget lookup on invalid state"))
    with pytest.raises(OSError):
        check.CatalogueCheck(driver.repo, driver.out, driver.archive / "baseline")


def test_changed_candidate_or_legacy_state_cannot_reuse_old_coverage(driver):
    driver.save()
    (driver.repo / "prompts" / "CATALOGUE_MANIFEST.jsonl").write_text(
        json.dumps({"id": "changed", "category": "one"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="different candidate identity"):
        check.CatalogueCheck(driver.repo, driver.out, driver.archive / "baseline")
    driver.out.write_text(json.dumps({"outcomes": {}}), encoding="utf-8")
    with pytest.raises(ValueError, match="legacy or different"):
        check.CatalogueCheck(driver.repo, driver.out, driver.archive / "baseline")


def test_budget_stop_is_incomplete_and_never_has_success_summary(driver, monkeypatch):
    monkeypatch.setattr(check.matched_study, "key_state", lambda: {"limit_remaining": 0.01})
    with pytest.raises(ValueError, match="stopped for budget"):
        driver.run()
    assert "summary" not in driver.state and not driver.state["outcomes"]


@pytest.mark.parametrize("partial_output", [False, True])
def test_interrupted_child_preserves_checkpoint_and_blocks_ambiguous_resume(driver, monkeypatch, partial_output):
    def first(root, command):
        _run(root / "run-first", [_result(IDS[0], "CLOSED_CANCELLED")])
        return 1

    def interrupted(root, command):
        if partial_output:
            _run(root / "run-interrupted", [_result(IDS[1])], category_filter=None, prompt_id_filter=IDS[1])
        raise KeyboardInterrupt()

    calls = _child(monkeypatch, [first, interrupted])
    with pytest.raises(KeyboardInterrupt):
        driver.run()
    saved = json.loads(driver.out.read_text())
    assert set(saved["outcomes"]) == {IDS[0]}
    assert len(saved["runs"]) == 2 and saved["runs"][-1]["exit"] is None
    monkeypatch.setattr(check.matched_study, "key_state", lambda: pytest.fail("no lookup on ambiguous state"))
    with pytest.raises(ValueError, match="unresolved child.*preserv"):
        check.CatalogueCheck(driver.repo, driver.out, driver.archive / "baseline")
    assert len(calls) == 2
    assert list(driver.archive.rglob("run-interrupted")) if partial_output else not list(
        driver.archive.rglob("run-interrupted"))


def test_pending_reservation_blocks_resume_even_without_output(driver, monkeypatch):
    driver.state["runs"].append({"args": ["--category", "one"], "requested": IDS, "exit": None, "run": None,
                                 "log": "retained.log"})
    driver.save()
    monkeypatch.setattr(check.subprocess, "run", lambda *a, **kw: pytest.fail("no new child"))
    with pytest.raises(ValueError, match="unresolved child"):
        check.CatalogueCheck(driver.repo, driver.out, driver.archive / "baseline")
