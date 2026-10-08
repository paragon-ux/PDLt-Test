"""A run records the code it executed (TARGET_ARCHITECTURE I-9; GOAL T0.4).

Each test builds a throwaway git repository, so the result never depends on the
state of this checkout."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import run_catalogue


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "t")
    (root / "harness.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "base")
    return root


def test_a_clean_tree_records_its_commit_and_no_difference(repo: Path, tmp_path: Path) -> None:
    provenance = run_catalogue.code_provenance(repo)
    assert provenance["commit"] == _git(repo, "rev-parse", "HEAD")
    assert provenance["dirty"] is False and provenance["diff_sha256"] is None
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    record = run_catalogue.record_provenance(run_dir, provenance)
    assert record["commit"] == provenance["commit"] and record["diff_file"] is None
    assert not (run_dir / run_catalogue.WORKTREE_DIFF).exists()


def test_a_dirty_run_records_the_commit_and_the_difference(repo: Path, tmp_path: Path) -> None:
    (repo / "harness.py").write_text("VALUE = 2\n", encoding="utf-8")
    (repo / "added.py").write_text("NEW = True\n", encoding="utf-8")
    provenance = run_catalogue.code_provenance(repo)
    assert provenance["dirty"] is True
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    record = run_catalogue.record_provenance(run_dir, provenance)
    meta = json.loads(json.dumps({"code": record}))  # what RUN_META.json stores
    assert meta["code"]["commit"] == _git(repo, "rev-parse", "HEAD")
    stored = (run_dir / meta["code"]["diff_file"]).read_text(encoding="utf-8")
    assert "-VALUE = 1" in stored and "+VALUE = 2" in stored  # the tracked change
    assert "+NEW = True" in stored  # an untracked file runs too
    assert [u["path"] for u in meta["code"]["untracked"]] == ["added.py"]
    import hashlib
    assert meta["code"]["diff_sha256"] == hashlib.sha256(stored.encode("utf-8")).hexdigest()


def test_a_dirty_tree_is_refused_unless_allowed(repo: Path) -> None:
    (repo / "harness.py").write_text("VALUE = 3\n", encoding="utf-8")
    provenance = run_catalogue.code_provenance(repo)
    with pytest.raises(SystemExit):
        run_catalogue.refuse_dirty_tree(provenance, allow_dirty=False)
    run_catalogue.refuse_dirty_tree(provenance, allow_dirty=True)  # allowed and recorded
    run_catalogue.refuse_dirty_tree(run_catalogue.code_provenance(repo.parent / "absent"), allow_dirty=False)


class _Stop(Exception):
    pass


def _start_run(monkeypatch, tmp_path: Path, repo: Path, argv: list[str]) -> Path:
    """Run the catalogue runner's main() up to its first prompt, against ``repo``."""
    monkeypatch.setattr(run_catalogue, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(run_catalogue, "code_provenance", lambda root=None: _real(repo))

    def stop(*args, **kwargs):
        raise _Stop

    monkeypatch.setattr(run_catalogue, "run_single_prompt", stop)
    monkeypatch.setattr("sys.argv", ["run_catalogue.py", "--prompt-id", "16-06", *argv])
    with pytest.raises(_Stop):
        run_catalogue.main()
    (run_dir,) = (tmp_path / "runs").iterdir()
    return run_dir


_real = run_catalogue.code_provenance


def test_the_runner_records_the_commit_and_difference_in_run_meta(monkeypatch, repo: Path, tmp_path: Path) -> None:
    (repo / "harness.py").write_text("VALUE = 4\n", encoding="utf-8")
    run_dir = _start_run(monkeypatch, tmp_path, repo, ["--allow-dirty"])
    meta = json.loads((run_dir / "RUN_META.json").read_text(encoding="utf-8"))
    assert meta["code"]["commit"] == _git(repo, "rev-parse", "HEAD") and meta["code"]["dirty"] is True
    assert "+VALUE = 4" in (run_dir / meta["code"]["diff_file"]).read_text(encoding="utf-8")


def test_the_runner_refuses_a_dirty_tree_without_the_flag(monkeypatch, repo: Path, tmp_path: Path) -> None:
    (repo / "harness.py").write_text("VALUE = 5\n", encoding="utf-8")
    monkeypatch.setattr(run_catalogue, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(run_catalogue, "code_provenance", lambda root=None: _real(repo))
    monkeypatch.setattr("sys.argv", ["run_catalogue.py", "--prompt-id", "16-06"])
    with pytest.raises(SystemExit) as refused:
        run_catalogue.main()
    assert "uncommitted" in str(refused.value)
    assert not (tmp_path / "runs").exists()  # nothing was started


@pytest.mark.parametrize("env", [None, "0"])
@pytest.mark.parametrize("tier_d1", [True, False])
def test_the_recorded_tier_d1_is_what_the_harness_runs_with(monkeypatch, tmp_path: Path, env, tier_d1) -> None:
    """The runner always sends the flag, so an explicit value beats the harness default and
    $PDLT_TIER_D1, and RUN_META cannot disagree with the process it started."""
    from pdl_taskmaster.host import repl
    from pdl_taskmaster.providers.api_worker import ApiWorker

    if env is None:
        monkeypatch.delenv("PDLT_TIER_D1", raising=False)
    else:
        monkeypatch.setenv("PDLT_TIER_D1", env)
    cmd = run_catalogue.build_harness_command(
        tmp_path / "p.txt", "s", tmp_path / "t.txt", tmp_path / "d", "m", "low",
        run_settings={"route": "confirmed", "tier_d1": tier_d1})
    settings = repl._api_run_settings(repl._build_parser().parse_args(cmd[3:]))
    assert settings["tier_d1"] is tier_d1
    assert ApiWorker(repo_root=tmp_path, model="m", tier_d1=settings["tier_d1"]).tier_d1 is tier_d1


def test_the_flag_is_left_out_for_control_and_for_legacy_settings(tmp_path: Path) -> None:
    base = (tmp_path / "p.txt", "s", tmp_path / "t.txt", tmp_path / "d", "m", "low")
    for settings in ({"route": "control", "tier_d1": False}, {"route": "control", "tier_d1": True}, {}, None):
        cmd = run_catalogue.build_harness_command(*base, run_settings=settings)
        assert "--tier-d1" not in cmd and "--no-tier-d1" not in cmd


@pytest.mark.parametrize("argv, expected, suffix", [
    ([], True, "-confirmed-tier-d1"),
    (["--no-tier-d1"], False, "-confirmed"),
    (["--route", "control"], False, "-control"),
    (["--route", "unconfirmed", "--draft-execute"], True, "-unconfirmed-draft-execute-tier-d1"),
])
def test_run_meta_and_the_run_name_state_the_tier_d1_the_harness_gets(
        monkeypatch, repo: Path, tmp_path: Path, argv, expected, suffix) -> None:
    monkeypatch.delenv("PDLT_TIER_D1", raising=False)
    run_dir = _start_run(monkeypatch, tmp_path, repo, argv)
    meta = json.loads((run_dir / "RUN_META.json").read_text(encoding="utf-8"))
    assert meta["run_settings"]["tier_d1"] is expected
    assert run_dir.name.endswith(suffix)


def test_tier_d1_environment_is_a_default_not_an_override(monkeypatch, tmp_path: Path) -> None:
    from pdl_taskmaster.providers.api_worker import ApiWorker

    monkeypatch.setenv("PDLT_TIER_D1", "0")
    assert ApiWorker(repo_root=tmp_path, model="m").tier_d1 is False
    assert ApiWorker(repo_root=tmp_path, model="m", tier_d1=True).tier_d1 is True
    monkeypatch.delenv("PDLT_TIER_D1")
    assert ApiWorker(repo_root=tmp_path, model="m").tier_d1 is True
