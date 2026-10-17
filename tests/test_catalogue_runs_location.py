"""Catalogue runs live outside the repository (the user, 2026-10-17): $PDLT_CATALOGUE_RUNS, else
PDLt-Catalogue-Archive beside the checkout. The runner writes there; the viewer reads there."""
from __future__ import annotations

import json
from pathlib import Path

import catalogue_runs
import run_catalogue
from viewer import server

ROOT = Path(__file__).resolve().parents[1]


def test_runs_are_written_outside_the_repository(monkeypatch):
    assert run_catalogue.RUNS_DIR == catalogue_runs.RUNS_DIR
    monkeypatch.delenv("PDLT_CATALOGUE_RUNS", raising=False)
    assert not catalogue_runs.runs_dir().resolve().is_relative_to(ROOT.resolve())


def test_the_location_is_configurable(monkeypatch, tmp_path):
    monkeypatch.setenv("PDLT_CATALOGUE_RUNS", str(tmp_path / "runs"))
    assert catalogue_runs.runs_dir() == tmp_path / "runs"
    monkeypatch.delenv("PDLT_CATALOGUE_RUNS")
    assert catalogue_runs.runs_dir() == ROOT.parent / "PDLt-Catalogue-Archive"


def test_the_viewer_reads_runs_kept_outside_its_root(monkeypatch, tmp_path):
    archive = tmp_path / "archive"
    result = archive / "run-20260101-000000" / "results" / "01-01_demo"
    result.mkdir(parents=True)
    (result / "result.json").write_text(json.dumps({"id": "01-01"}), encoding="utf-8")
    monkeypatch.setenv("PDLT_CATALOGUE_RUNS", str(archive))
    root = tmp_path / "repo"
    root.mkdir()
    assert [r["id"] for r in server.list_runs(root)] == ["run-20260101-000000"]
    (item,) = server.read_run(root, "run-20260101-000000")["results"]
    assert item["path"] == result.resolve().as_posix()
