"""The frozen prompt set of the acceptance gate (design §6), with a hash per file.

``python -m experiments.prompt_set --write`` writes ``experiments/PROMPT_SET.lock.json``.
``--check`` verifies that the committed lock still matches every file, so no
gate prompt can change after the lock was committed.

The strata follow the selection rule in §6.1: only the grader's ability to
return both PASS and FAIL decides them. Model results never do.

The famous tiers are **proposed** (rater 1). A second rater confirms or changes
them before Day 1. They only drive descriptive reporting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "prompts"
GENERATED = Path(__file__).resolve().parent / "prompts"
LOCK_PATH = Path(__file__).resolve().parent / "PROMPT_SET.lock.json"

STRATA: dict[str, list[str]] = {
    # T: decisive catalogue task prompts (grader returns both PASS and FAIL).
    "T": ["01-01", "01-02", "01-03", "01-04", "01-05", "01-06", "01-07",
          "13-01", "13-02", "13-04", "14-01", "14-03", "14-05", "14-07",
          "16-03", "16-05", "16-06", "16-07"],
    # S: safety and containment, graded.
    "S": ["13-03", "13-05", "13-06", "13-07"],
    # I: injection prompts, adjudicated with the two-part rubric (rubrics/injection.md).
    "I": ["09-01", "09-02", "09-03", "09-04", "09-05", "09-06", "09-07"],
    # Q: qualitative; the grader cannot return one of PASS or FAIL. Never in a decision rule.
    "Q": ["14-02", "14-04", "14-06", "16-01", "16-02", "16-04"],
}
FAMOUS_TIERS: dict[str, list[str]] = {
    "F": ["16-01", "16-02", "16-04", "16-05", "16-06", "14-07", "13-04"],
    "R": ["16-03", "16-07", "14-01", "14-03", "14-05", "13-01", "13-02"],
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _catalogue_files() -> dict[str, str]:
    files = {}
    for line in (CATALOGUE / "CATALOGUE_MANIFEST.jsonl").read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            entry = json.loads(line)
            files[entry["id"]] = entry["file"]
    return files


def _generated(name: str) -> list[dict[str, Any]]:
    lines = (GENERATED / name / "MANIFEST.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def tier_of(item_id: str) -> str:
    for tier, ids in FAMOUS_TIERS.items():
        if item_id in ids:
            return tier
    return "N"


def build_lock() -> dict[str, Any]:
    files = _catalogue_files()
    items: list[dict[str, Any]] = []
    for stratum, ids in STRATA.items():
        for item_id in ids:
            path = CATALOGUE / files[item_id]
            items.append({"id": item_id, "set": "gate", "stratum": stratum, "tier": tier_of(item_id),
                          "file": f"prompts/{files[item_id]}", "sha256": _sha256(path)})
    for name, stratum in (("gate", "G"), ("dev", "DEV")):
        for entry in _generated(name):
            path = GENERATED / entry["file"]
            items.append({"id": entry["id"], "set": name, "stratum": stratum, "tier": "N",
                          "family": entry["family"], "template": entry["template"],
                          "file": f"experiments/prompts/{entry['file']}", "sha256": _sha256(path)})
    return {
        "version": 1,
        "design": "docs/plans/protocol-vs-control-experiment-design.md",
        "decision_strata": {"G1": ["S", "I"], "G2": ["T", "G"], "G4": ["T", "G"]},
        "famous_tiers_status": "proposed by rater 1; a second rater confirms before Day 1",
        "counts": {s: sum(1 for i in items if i["stratum"] == s) for s in ("T", "G", "S", "I", "Q", "DEV")},
        "items": items,
    }


def check_lock() -> list[str]:
    if not LOCK_PATH.is_file():
        return [f"{LOCK_PATH.name} is missing"]
    committed = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    current = build_lock()
    problems = []
    old = {i["id"]: i for i in committed.get("items", [])}
    new = {i["id"]: i for i in current["items"]}
    for item_id in sorted(set(old) | set(new)):
        if item_id not in new:
            problems.append(f"{item_id}: in the lock but no longer in the set")
        elif item_id not in old:
            problems.append(f"{item_id}: in the set but not in the lock")
        elif old[item_id] != new[item_id]:
            problems.append(f"{item_id}: changed since the lock ({old[item_id].get('sha256', '')[:12]} -> "
                            f"{new[item_id]['sha256'][:12]})")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        LOCK_PATH.write_text(json.dumps(build_lock(), indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {LOCK_PATH}")
        return 0
    problems = check_lock()
    for problem in problems:
        print(problem)
    print("prompt set matches its lock" if not problems else f"{len(problems)} differences")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
