"""Where catalogue and experiment runs are written and read: outside the repository, so it stays focused and easy to
review (the user, 2026-10-17). ``$PDLT_CATALOGUE_RUNS`` names the folder; the default is ``PDLt-Catalogue-Archive``
beside the repository checkout. The folder holds one entry per run (``run-<timestamp>-<label>/``, ``sweep-logs/``,
``plan-gate-<timestamp>/`` and so on), as ``catalogue-runs/`` did before it was archived."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARCHIVE_NAME = "PDLt-Catalogue-Archive"


def runs_dir(repo_root: Path | None = None) -> Path:
    configured = os.environ.get("PDLT_CATALOGUE_RUNS")
    return Path(configured).expanduser() if configured else (repo_root or ROOT).parent / ARCHIVE_NAME


RUNS_DIR = runs_dir()
