"""Evaluation-plane graders: PASS on solution-file data, FAIL on corrupted data."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import graders

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "prompts"
MANIFEST = {
    json.loads(l)["id"]: json.loads(l)
    for l in (PROMPTS / "CATALOGUE_MANIFEST.jsonl").read_text(encoding="utf-8-sig").splitlines()
    if l.strip()
}


def _solution(entry_id: str) -> dict:
    return json.loads((PROMPTS / MANIFEST[entry_id]["solution_file"]).read_text(encoding="utf-8-sig"))


def _run_dir(tmp_path: Path, deliverable: str | None) -> Path:
    if deliverable is not None:
        out = tmp_path / "session" / "turns" / "turn_001" / "stages" / "50_execution" / "output"
        out.mkdir(parents=True)
        (out / "current.md").write_text(deliverable, encoding="utf-8")
    return tmp_path


def _grade(entry_id: str, tmp_path: Path, deliverable: str | None) -> str:
    result = graders.grade(MANIFEST[entry_id], _run_dir(tmp_path, deliverable), PROMPTS, run_code=False)
    return result["grade"]


def test_every_verified_entry_has_a_grader_or_manual_marker():
    verified = [e for e in MANIFEST.values() if e["ground_truth_status"] == "verified"]
    assert len(verified) == 21
    machine = [e["id"] for e in verified if e["id"] in graders.GRADERS]
    assert machine == ["01-01", "01-02", "01-03", "01-04", "01-05", "01-06", "01-07", "13-01"]


def test_non_verified_entries_are_not_applicable(tmp_path):
    assert graders.grade(MANIFEST["06-04"], tmp_path, PROMPTS)["grade"] == graders.NA


def test_manual_for_verified_without_machine_check(tmp_path):
    assert graders.grade(MANIFEST["14-01"], tmp_path, PROMPTS)["grade"] == graders.MANUAL


def test_missing_deliverable_fails(tmp_path):
    assert _grade("01-01", tmp_path, None) == graders.FAIL


def test_01_01_partition(tmp_path):
    triples = _solution("01-01")["witness"]
    body = "Result:\n```json\n" + json.dumps({"witness": {"data": {"triples": triples}}}) + "\n```"
    assert _grade("01-01", tmp_path, body) == graders.PASS
    bad = [list(t) for t in triples]
    bad[0][2] += 1
    assert _grade("01-01", tmp_path / "b", "```json\n" + json.dumps({"triples": bad}) + "\n```") == graders.FAIL


def test_01_02_exact_covers(tmp_path):
    covers = [w["cover"] for w in _solution("01-02")["witnesses"]]
    assert _grade("01-02", tmp_path, "\n".join(", ".join(c) for c in covers)) == graders.PASS
    assert _grade("01-02", tmp_path / "b", ", ".join(covers[0]) + "\n" + ", ".join(covers[1])) == graders.FAIL
    assert _grade("01-02", tmp_path / "c", "\n".join(", ".join(c) for c in covers) + "\nS1, S5, S9") == graders.FAIL


def test_01_03_coloring(tmp_path):
    coloring = _solution("01-03")["example_coloring"]
    assert _grade("01-03", tmp_path, json.dumps(coloring)) == graders.PASS
    bad = dict(coloring)
    bad["1"] = bad["0"]
    assert _grade("01-03", tmp_path / "b", json.dumps(bad)) == graders.FAIL


def test_01_04_subset_sum(tmp_path):
    import itertools

    S = [3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21]
    subsets = [list(c) for r in range(1, 13) for c in itertools.combinations(S, r) if sum(c) == 40]
    assert len(subsets) == _solution("01-04")["solution_count"]
    body = "\n".join(str(s) for s in subsets) + f"\nTotal solutions: {len(subsets)}"
    assert _grade("01-04", tmp_path, body) == graders.PASS
    assert _grade("01-04", tmp_path / "b", "\n".join(str(s) for s in subsets[:5]) + "\nTotal: 5") == graders.FAIL


def test_01_05_latin_square(tmp_path):
    square = _solution("01-05")["original_complete_square"]
    assert _grade("01-05", tmp_path, "\n".join(str(r) for r in square)) == graders.PASS
    bad = [list(r) for r in square]
    bad[1][0], bad[1][1] = bad[1][1], bad[1][0]
    assert _grade("01-05", tmp_path / "b", "\n".join(str(r) for r in bad)) == graders.FAIL


def test_01_06_first_fit(tmp_path):
    optimal = [b["items"] for b in _solution("01-06")["optimal_result"]["packing"]]
    body = "First Fit uses 5 bins.\nOptimal uses 4 bins:\n" + "\n".join(str(b) for b in optimal)
    assert _grade("01-06", tmp_path, body) == graders.PASS
    assert _grade("01-06", tmp_path / "b", "First Fit uses 5 bins.\nOptimal: [[5, 5, 5], [3, 3, 3], [7], [7]]") == graders.FAIL


def test_01_07_hamiltonian(tmp_path):
    path = _solution("01-07")["hamiltonian_path"]
    assert _grade("01-07", tmp_path, f"Path: {path}") == graders.PASS
    bad = list(path)
    bad[3], bad[9] = bad[9], bad[3]
    assert _grade("01-07", tmp_path / "b", f"Path: {bad}") == graders.FAIL


def test_13_01_unsat(tmp_path):
    assert _grade("13-01", tmp_path, "The constraints are unsatisfiable: C1-C3 force all-different values.") == graders.PASS
    assert _grade("13-01", tmp_path / "b", "One solution is x=2, y=1, z=1.") == graders.FAIL
