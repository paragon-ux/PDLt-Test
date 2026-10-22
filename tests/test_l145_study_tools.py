"""L145: the study driver (schedule, preflight, outage handling, budget stop, resume), the report's statistics and the
power simulation, on synthetic worktrees, ledgers and run folders. Offline; no model or network call."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from experiments import analysis, matched_study, power_sim, study_report, study_stats
from experiments.schedule import MAX_BLOCK_RERUNS, Ledger

ROOT = Path(__file__).resolve().parents[1]


def _config(tmp_path: Path, **extra) -> dict:
    config = {"study": "T", "seed": 7, "repeats": 3, "prompts": ["01-01", "01-03", "02-01"], "out_dir": str(tmp_path / "out"),
              "arms": {"ON": {"worktree": str(tmp_path / "wt"), "commit": "HEAD", "args": ["--agent-tools"]},
                       "OFF": {"worktree": str(tmp_path / "wt"), "commit": "HEAD", "args": []},
                       "ON-x": {"worktree": str(tmp_path / "wt"), "commit": "HEAD", "args": ["--agent-tools"],
                                "repeats": [1]}},
              "budget": {"cap_usd": 1.0, "reserve_usd": 0.1, "per_run_usd": {"ON": 0.01, "OFF": 0.01, "ON-x": 0.01}}}
    config.update(extra)
    path = tmp_path / "study.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config), encoding="utf-8")
    return matched_study.load_config(path)


# ---- schedule

def test_the_schedule_is_fixed_by_the_seed_and_an_arm_runs_only_its_repeats(tmp_path):
    config = _config(tmp_path)
    first, again = matched_study.schedule(config), matched_study.schedule(config)
    assert matched_study.schedule_json(first) == matched_study.schedule_json(again)
    assert len(first) == 9 and [b.rep for b in first] == [1, 1, 1, 2, 2, 2, 3, 3, 3]
    assert all(("ON-x" in b.arms) == (b.rep == 1) for b in first)
    assert all(set(b.arms) - {"ON-x"} == {"ON", "OFF"} for b in first)
    other = _config(tmp_path, seed=8)
    assert matched_study.schedule_json(matched_study.schedule(other)) != matched_study.schedule_json(first)
    est = matched_study.estimate(config, first)
    assert est["runs"] == {"OFF": 9, "ON": 9, "ON-x": 3} and est["total_runs"] == 21


# ---- preflight

def _worktree(path: Path, *, package: bool = True) -> str:
    path.mkdir(parents=True)
    (path / "run_catalogue.py").write_text(
        "import sys\nif '--dry-run' in sys.argv:\n    print(sys.argv[sys.argv.index('--prompt-id') + 1])\n",
        encoding="utf-8")
    if package:
        (path / "src" / "pdl_taskmaster").mkdir(parents=True)
        (path / "src" / "pdl_taskmaster" / "__init__.py").write_text("", encoding="utf-8")
    for args in (["init", "-q"], ["add", "-A"], ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"]):
        subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)
    return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def _arm_problems(config) -> list[str]:
    return [p for p in matched_study.preflight(config, check_key=False) if not p.startswith("the driver's checkout")]


def test_preflight_passes_a_clean_worktree_at_its_commit_with_its_own_package(tmp_path):
    commit = _worktree(tmp_path / "wt")
    config = _config(tmp_path, arms={"A": {"worktree": str(tmp_path / "wt"), "commit": commit, "args": []}})
    matched_study.schedule_path(config).write_text(matched_study.schedule_json(matched_study.schedule(config)))
    assert _arm_problems(config) == []


def test_preflight_refuses_a_dirty_tree_a_wrong_commit_and_a_foreign_package(tmp_path):
    commit = _worktree(tmp_path / "wt")
    _worktree(tmp_path / "bare", package=False)
    (tmp_path / "wt" / "stray.txt").write_text("x", encoding="utf-8")
    config = _config(tmp_path, arms={"A": {"worktree": str(tmp_path / "wt"), "commit": "HEAD~0", "args": []},
                                     "B": {"worktree": str(tmp_path / "bare"), "commit": commit, "args": []}})
    problems = _arm_problems(config)
    assert any("missing or differs" in p for p in problems)
    assert any(p.startswith("A:") and "uncommitted" in p for p in problems)
    assert any(p.startswith("B:") and "is at" in p for p in problems)  # not the commit it was given
    assert any(p.startswith("B:") and "would import pdl_taskmaster from" in p for p in problems)


def test_preflight_names_a_file_that_differs_between_arms(tmp_path):
    a, b = _worktree(tmp_path / "a"), _worktree(tmp_path / "b")
    config = _config(tmp_path, arms={"A": {"worktree": str(tmp_path / "a"), "commit": a, "args": []},
                                     "B": {"worktree": str(tmp_path / "b"), "commit": b, "args": []}},
                     same_files=["run_catalogue.py", "src/pdl_taskmaster/__init__.py"])
    matched_study.schedule_path(config).write_text(matched_study.schedule_json(matched_study.schedule(config)))
    assert _arm_problems(config) == []
    (tmp_path / "b" / "run_catalogue.py").write_text("print(1)\n", encoding="utf-8")
    assert any(p.startswith("run_catalogue.py differs") for p in _arm_problems(config))


# ---- outages

def _run_dir(root: Path, result: dict, events: list[dict] | None = None) -> Path:
    folder = root / "run-x" / "results" / "01-01_x"
    folder.mkdir(parents=True)
    (folder / "result.json").write_text(json.dumps(result), encoding="utf-8")
    if events is not None:
        (folder / "session").mkdir()
        (folder / "session" / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    return root / "run-x"


def test_only_failures_that_are_never_model_outcomes_are_outages(tmp_path):
    unavailable = {"verdict": "HARNESS_ERROR", "harness_error": {"category": "PROVIDER_UNAVAILABLE", "status": 503}}
    assert "provider unavailable" in matched_study.classify(_run_dir(tmp_path / "a", unavailable), [])["outage"]
    for result in ({"verdict": "HARNESS_ERROR", "harness_error": {"category": "OUTPUT_LIMIT_REACHED"}},
                   {"verdict": "TIMEOUT"}, {"verdict": "CLOSED_CANCELLED"},
                   {"verdict": "HARNESS_ERROR", "harness_error": {"category": "PROVIDER_REJECTED_REQUEST"}}):
        assert "outage" not in matched_study.classify(_run_dir(tmp_path / result["verdict"] /
                                                               str(id(result)), result), [])
    control = ["--route", "control"]
    no_generation = [{"kind": "MODEL_OUTPUT_RECORDED", "payload": {"response_id": None}}]
    with_generation = [{"kind": "MODEL_OUTPUT_RECORDED", "payload": {"response_id": "gen-1"}}]
    ok = {"verdict": "CLOSED_SUCCESS"}
    assert matched_study.classify(_run_dir(tmp_path / "c1", ok, no_generation), control)["outage"]
    assert "outage" not in matched_study.classify(_run_dir(tmp_path / "c2", ok, with_generation), control)
    assert matched_study.classify(None, [])["outage"] == "no run folder"


def _scripted_run(monkeypatch, config, outcomes):
    """run_unit replaced by a script: ``outcomes`` maps (block_id, arm, attempt) to an outage reason."""
    calls = []

    def run_unit(config, block, arm, attempt, logs):
        calls.append((block.block_id, arm, attempt))
        reason = outcomes.get((block.block_id, arm, attempt))
        row = {"block_id": block.block_id, "attempt": attempt, "arm": arm, "branch": None, "item": block.item_id,
               "rep": block.rep, "status": "done", "run_dir": "x", "wall_s": 0.0, "verdict": "CLOSED_SUCCESS",
               "grade": "PASS"}
        return {**row, "outage": reason} if reason else row

    monkeypatch.setattr(matched_study, "run_unit", run_unit)
    monkeypatch.setattr(matched_study, "preflight", lambda config, **kw: [])
    monkeypatch.setattr(matched_study, "OUTAGE_BACKOFF_S", 0)
    monkeypatch.setattr(matched_study, "_manifest", lambda config, blocks, key: {"key_at_start": key})
    monkeypatch.setattr(matched_study, "key_state", lambda: {"usage": 1.0, "limit": 25, "limit_remaining": 20.0})
    return calls


def test_an_outage_voids_the_block_which_is_rerun_whole(tmp_path, monkeypatch):
    config = _config(tmp_path)
    first = matched_study.schedule(config)[0]
    calls = _scripted_run(monkeypatch, config, {(first.block_id, first.arms[-1], 1): "provider unavailable (503)"})
    args = type("A", (), {"max_blocks": 1})()
    assert matched_study.cmd_run(config, args) == 3  # one block of nine done
    ledger = Ledger(matched_study.out_dir(config) / "ledger.jsonl")
    assert ledger.attempt(first.block_id) == 2
    assert [c for c in calls if c[2] == 2] == [(first.block_id, arm, 2) for arm in first.arms]  # every arm again
    assert {r["arm"] for r in ledger.results() if r["block_id"] == first.block_id} == set(first.arms)
    assert all(r["attempt"] == 2 for r in ledger.results())


def test_a_block_failing_after_its_reruns_is_kept_and_flagged(tmp_path, monkeypatch):
    config = _config(tmp_path)
    first = matched_study.schedule(config)[0]
    arm = first.arms[0]
    _scripted_run(monkeypatch, config, {(first.block_id, arm, a): "provider unavailable (503)"
                                        for a in range(1, MAX_BLOCK_RERUNS + 2)})
    matched_study.cmd_run(config, type("A", (), {"max_blocks": 1})())
    rows = Ledger(matched_study.out_dir(config) / "ledger.jsonl").results()
    kept = [r for r in rows if r["arm"] == arm]
    assert len(kept) == 1 and kept[0]["kept_after_reruns"] and kept[0]["attempt"] == MAX_BLOCK_RERUNS + 1


def test_a_run_resumes_at_the_first_unfinished_block_and_stops_on_the_budget(tmp_path, monkeypatch):
    config = _config(tmp_path)
    calls = _scripted_run(monkeypatch, config, {})
    matched_study.cmd_run(config, type("A", (), {"max_blocks": 2})())
    assert matched_study.cmd_run(config, type("A", (), {"max_blocks": None})()) == 0
    assert len(calls) == len(set(calls)) == 21  # nothing run twice
    monkeypatch.setattr(matched_study, "key_state", lambda: {"usage": 1.0, "limit": 25, "limit_remaining": 0.05})
    fresh = _config(tmp_path / "second")
    assert matched_study.cmd_run(fresh, type("A", (), {"max_blocks": None})()) == 3


# ---- statistics

def test_the_exact_sign_flip_test_matches_enumeration_and_holm_is_step_down():
    import random

    rng = random.Random(3)
    for _ in range(100):
        diffs = [rng.choice([-3, -2, -1, 0, 1, 2, 3]) / 3 for _ in range(rng.randint(1, 14))]
        assert study_stats.sign_flip_p(diffs, 3) == pytest.approx(analysis.sign_flip_p(diffs))
    assert study_stats.holm({"H1": 0.04, "H2": 0.01}) == {"H2": 0.02, "H1": 0.04}
    assert study_stats.holm({"H1": 0.03, "H2": 0.02}) == {"H2": 0.04, "H1": 0.04}  # monotone
    with pytest.raises(ValueError):
        study_stats.sign_flip_p([0.5], 3)


def test_a_prompt_contrast_by_hand():
    a = {"p1": [1, 1, 1], "p2": [0, 1, 1], "p3": [0, 0, 0]}
    b = {"p1": [0, 0, 0], "p2": [0, 1, 1], "p3": [1, 0, 0]}
    c = study_stats.prompt_contrast(a, b, repeats=3, n_boot=2000)
    assert c["effect"] == pytest.approx((1 + 0 - 1 / 3) / 3)
    assert (c["ahead"], c["behind"], c["tied"]) == (1, 1, 1)
    assert c["p"] == pytest.approx(1.0)  # observed sum 3 - 1 = 2; every sign pattern of (3, 1) reaches it
    runs = study_stats.run_mcnemar({("p1", 1): 1, ("p3", 1): 0}, {("p1", 1): 0, ("p3", 1): 1})
    assert (runs["only_a"], runs["only_b"]) == (1, 1)


# ---- the report on synthetic runs

def test_the_report_from_a_ledger_and_its_run_folders(tmp_path, monkeypatch):
    config = _config(tmp_path, prompts=["01-01", "01-03"],
                     analysis={"contrasts": [{"label": "tools", "a": "ON", "b": "OFF"}],
                               "screens": [{"label": "x", "arm": "ON-x", "reference": "ON"}],
                               "primary": {"a": "ON", "b": "OFF", "prompt_set": "all",
                                           "endpoints": {"H1": "pass", "H2": "sfp"}},
                               "b_rule": {"candidates": ["OFF", "ON"], "configs": {"OFF": "b.json", "ON": "b-on.json"}}})
    ledger = Ledger(matched_study.out_dir(config) / "ledger.jsonl")
    outcome = {"ON": ("CLOSED_SUCCESS", "PASS"), "OFF": ("CLOSED_SUCCESS", "FAIL"), "ON-x": ("CLOSED_CANCELLED", "FAIL")}
    for block in matched_study.schedule(config):
        for arm in block.arms:
            verdict, grade = outcome[arm]
            folder = tmp_path / "runs" / block.block_id.replace(":", "_") / arm
            folder.mkdir(parents=True)
            (folder / "result.json").write_text(json.dumps({
                "id": block.item_id, "verdict": verdict, "expected_stage": "CLOSED_SUCCESS",
                "ground_truth_grade": {"grade": grade}, "elapsed_seconds": 2.0}), encoding="utf-8")
            ledger.append({"block_id": block.block_id, "attempt": 1, "arm": arm, "branch": None, "status": "done",
                           "item": block.item_id, "rep": block.rep, "result_dir": str(folder)})
    monkeypatch.setattr(study_report.graders, "grade",
                        lambda entry, folder, prompts: json.loads((Path(folder) / "result.json").read_text())
                        ["ground_truth_grade"])
    report, problems, _ = study_report.build(config, lookup=False)
    assert problems == []
    assert report["arms"]["ON"]["passes"] == 6 and report["arms"]["OFF"]["sfp"] == 6
    h1, h2 = report["primary"]["tests"]["H1"], report["primary"]["tests"]["H2"]
    assert h1["effect"] == 1.0 and h2["effect"] == -1.0 and h1["p"] == pytest.approx(0.5)
    screen = next(s for s in report["screens"] if s["endpoint"] == "pass")
    assert screen["screen_total"] == 0 and screen["reference_same_block_total"] == 2
    assert report["b_rule"]["chosen"] == "ON" and report["b_rule"]["chosen_config"] == "b-on.json"
    assert [c["arm"] for c in report["b_rule"]["ranking"]] == ["ON", "OFF"]
    assert "Data problems" in study_report.markdown(config, report, problems, [])


# ---- power

def test_the_power_simulation_is_seeded(tmp_path):
    rows = [{"variant": v, "id": f"p{i}", "repeat": k, "passed": (v == "U") or i % 2, "verdict": "CLOSED_SUCCESS",
             "grade": "PASS" if (v == "U") or i % 2 else "FAIL"} for v in "UC" for i in range(6) for k in (1, 2, 3)]
    path = tmp_path / "L94.json"
    path.write_text(json.dumps({"rows": rows}), encoding="utf-8")
    ids, table = power_sim.rates(path)
    assert len(ids) == 6 and table["p0"]["C"] == (0.0, 1.0)
    import random

    one = power_sim.power(ids, table, endpoint=0, repeats=3, prompts=None, sims=50, rng=random.Random(1))
    two = power_sim.power(ids, table, endpoint=0, repeats=3, prompts=None, sims=50, rng=random.Random(1))
    assert one == two and 0.0 <= one <= 1.0
