"""F8: changed studies cannot resume or aggregate an earlier study's measurements. Offline."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments import matched_study, study_report
from experiments.schedule import Ledger
from test_l145_study_tools import _config, _scripted_run


@pytest.fixture
def partial(tmp_path, monkeypatch):
    config = _config(tmp_path, prompts=["01-01"], repeats=2,
                     arms={"A": {"worktree": str(tmp_path / "wt"), "commit": "self", "args": []}})
    calls = _scripted_run(monkeypatch, config, {})
    assert matched_study.cmd_run(config, SimpleNamespace(max_blocks=1)) == 3
    return config, calls


@pytest.mark.parametrize("change", ["shared_args", "arm_args", "seed", "arm_commit", "arm_set"])
def test_changed_config_is_refused_before_preflight_or_budget(partial, monkeypatch, change):
    config, calls = partial
    out = matched_study.out_dir(config)
    before = {p.name: p.read_bytes() for p in (out / "ledger.jsonl", out / "STUDY_MANIFEST.json")}
    raw = {k: v for k, v in config.items() if k != "_path"}
    if change == "shared_args":
        raw["shared_args"] = ["--reasoning", "medium"]
    elif change == "arm_args":
        raw["arms"]["A"]["args"] = ["--no-agent-tools"]
    elif change == "seed":
        raw["seed"] += 1
    elif change == "arm_commit":
        raw["arms"]["A"]["commit"] = "another-commit"
    else:
        raw["arms"]["B"] = dict(raw["arms"]["A"])
    Path(config["_path"]).write_text(json.dumps(raw), encoding="utf-8")
    changed = matched_study.load_config(Path(config["_path"]))
    monkeypatch.setattr(matched_study, "preflight", lambda *a, **k: pytest.fail("must validate identity first"))
    monkeypatch.setattr(matched_study, "key_state", lambda: pytest.fail("no budget/network call on mismatch"))
    assert matched_study.cmd_run(changed, SimpleNamespace(max_blocks=None)) == 1
    with pytest.raises(ValueError, match="study identity invalid"):
        study_report.build(changed, lookup=False)
    assert len(calls) == 1
    assert all((out / name).read_bytes() == data for name, data in before.items())


@pytest.mark.parametrize("change", ["source", "driver", "schedule", "missing_manifest", "corrupt_manifest"])
def test_resume_refuses_changed_execution_identity_and_preserves_rows(partial, monkeypatch, change):
    config, calls = partial
    out = matched_study.out_dir(config)
    ledger_bytes = (out / "ledger.jsonl").read_bytes()
    if change in {"source", "driver"}:
        def git(path, *args):
            is_driver = Path(path) == matched_study.ROOT
            return "changed-source" if is_driver == (change == "driver") else "frozen-source"
        monkeypatch.setattr(matched_study, "git", git)
    elif change == "schedule":
        matched_study.schedule_path(config).write_text("wrong schedule", encoding="utf-8")
    elif change == "missing_manifest":
        (out / "STUDY_MANIFEST.json").unlink()
    else:
        (out / "STUDY_MANIFEST.json").write_text("{", encoding="utf-8")
    monkeypatch.setattr(matched_study, "preflight", lambda *a, **k: pytest.fail("must validate identity first"))
    assert matched_study.cmd_run(config, SimpleNamespace(max_blocks=None)) == 1
    assert (out / "ledger.jsonl").read_bytes() == ledger_bytes and len(calls) == 1


def test_unchanged_partial_resume_keeps_completed_units(partial):
    config, calls = partial
    assert matched_study.cmd_run(config, SimpleNamespace(max_blocks=None)) == 0
    assert len(calls) == len(set(calls)) == 2


@pytest.mark.parametrize("change", ["duplicate", "unit_commit", "unit_settings"])
def test_reports_refuse_duplicate_or_mismatched_accepted_units(partial, monkeypatch, change):
    config, _ = partial
    assert matched_study.cmd_run(config, SimpleNamespace(max_blocks=None)) == 0
    ledger = Ledger(matched_study.out_dir(config) / "ledger.jsonl")
    rows = ledger.results()
    if change == "duplicate":
        ledger.append(rows[0])
    else:
        path = Path(rows[-1]["run_dir"]) / "RUN_META.json"
        meta = json.loads(path.read_text(encoding="utf-8"))
        if change == "unit_commit":
            meta["code"]["commit"] = "foreign-source"
        else:
            meta["run_settings"] = {"unexpected": True}
        path.write_text(json.dumps(meta), encoding="utf-8")
    monkeypatch.setattr(study_report.graders, "grade", lambda *a: pytest.fail("must refuse before grading"))
    with pytest.raises(ValueError, match="study identity invalid"):
        study_report.build(config, lookup=False)


def test_historical_identity_validation_uses_frozen_artifacts_after_config_move(partial, tmp_path, monkeypatch):
    config, _ = partial
    moved = tmp_path / "moved" / "study.json"
    moved.parent.mkdir()
    moved.write_bytes(Path(config["_path"]).read_bytes())
    historical = matched_study.load_config(moved)
    monkeypatch.setattr(matched_study, "git", lambda *a: pytest.fail("historical identity must not query Git"))
    frozen, identities = matched_study.validate_study(historical)
    assert frozen["arms"]["A"]["commit"] == "frozen-source" and "A" in identities


def test_invalid_report_cli_preserves_existing_outputs(partial, tmp_path):
    config, _ = partial
    (matched_study.out_dir(config) / "STUDY_MANIFEST.json").unlink()
    output = tmp_path / "report.json"
    output.write_text("preserved", encoding="utf-8")
    assert study_report.main([config["_path"], "--no-lookup", "--json", str(output)]) == 1
    assert output.read_text(encoding="utf-8") == "preserved"
