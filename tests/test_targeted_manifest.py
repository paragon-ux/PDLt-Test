"""L155: the targeted catalogue (prompts/TARGETED_MANIFEST.jsonl), a permanent separate test set: per category, its first
prompt and its highest recorded failure rate prompt, category 09 excluded (experiments/mode_study_prompts.py)."""
from __future__ import annotations

import json
from pathlib import Path

import run_catalogue

ROOT = Path(__file__).resolve().parents[1]
TARGETED = ROOT / "prompts" / "TARGETED_MANIFEST.jsonl"


def _lines(path: Path) -> dict[str, str]:
    return {json.loads(line)["id"]: line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def test_every_targeted_prompt_is_the_catalogues_own_entry():
    catalogue, targeted = _lines(ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl"), _lines(TARGETED)
    assert targeted and all(catalogue.get(pid) == line for pid, line in targeted.items())


def test_two_prompts_per_category_with_the_first_and_no_category_09():
    catalogue, targeted = _lines(ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl"), _lines(TARGETED)
    categories = sorted({pid[:2] for pid in catalogue} - {"09"})
    assert sorted({pid[:2] for pid in targeted}) == categories
    for prefix in categories:
        chosen = sorted(pid for pid in targeted if pid.startswith(prefix + "-"))
        assert len(chosen) == 2 and chosen[0] == min(pid for pid in catalogue if pid.startswith(prefix + "-"))


def test_the_runner_loads_it():
    entries = run_catalogue.load_manifest(path=run_catalogue._manifest_path("prompts/TARGETED_MANIFEST.jsonl"))
    assert len(entries) == len(_lines(TARGETED))
    assert all((ROOT / "prompts" / entry["file"]).is_file() for entry in entries)
