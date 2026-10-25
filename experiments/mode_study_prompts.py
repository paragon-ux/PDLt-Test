"""L155: the mode study's targeted prompt set (the user, 2026-10-23): per category, its first prompt (X-01) and the prompt
with the highest recorded failure rate, category 09 excluded (the gateway is measured in L153).

The failure rate is FAIL / runs (run_catalogue.outcome_class) over recorded runs of openai/gpt-oss-120b on the
unconfirmed route in the shipped configuration: no ablation, no withheld context, no in-call tools. Prompts with fewer
than MIN_RUNS runs are not candidates; ties go to more runs, then the lower id; the X-01 prompt is never the second pick.

    python experiments/mode_study_prompts.py [ARCHIVE] [--write]

``--write`` freezes the selection as prompts/TARGETED_MANIFEST.jsonl: the catalogue's own manifest lines for the chosen
prompts, run with ``run_catalogue.py --manifest prompts/TARGETED_MANIFEST.jsonl``. The frozen set is the permanent
targeted test; rerunning the selection on later data does not change it unless written again.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_RUNS = 3
EXCLUDED_CATEGORY = "09"


def shipped(meta: dict) -> bool:
    settings = meta.get("run_settings") or {}
    return (meta.get("model") == "openai/gpt-oss-120b" and meta.get("route") == "unconfirmed"
            and not settings.get("ablate_unconfirmed") and not settings.get("withhold_execution_context")
            and not settings.get("agent_tools"))


def failure_rates(archive: Path) -> dict[str, tuple[int, int]]:
    sys.path.insert(0, str(ROOT))
    import run_catalogue

    tally: dict[str, list[int]] = {}
    # Run folders sit at most three levels down (run-*, STUDY/run-*, STUDY/ARM/run-*); a recursive search would
    # walk every session folder.
    metas = [m for pattern in ("run-*/RUN_META.json", "*/run-*/RUN_META.json", "*/*/run-*/RUN_META.json")
             for m in archive.glob(pattern)]
    for meta_file in metas:
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not shipped(meta):
            continue
        for result_file in (meta_file.parent / "results").glob("*/result.json"):
            try:
                result = json.loads(result_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            pair = tally.setdefault(result_file.parent.name[:5], [0, 0])
            pair[0] += run_catalogue.outcome_class(result) == "FAIL"
            pair[1] += 1
    return {pid: (fails, runs) for pid, (fails, runs) in tally.items()}


def select(archive: Path) -> list[dict]:
    manifest = [json.loads(line) for line in (ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl").read_text(
        encoding="utf-8").splitlines() if line.strip()]
    rates = failure_rates(archive)
    chosen = []
    for prefix in sorted({entry["id"][:2] for entry in manifest} - {EXCLUDED_CATEGORY}):
        ids = sorted(entry["id"] for entry in manifest if entry["id"].startswith(prefix + "-"))
        first = ids[0]
        candidates = [(rates[i][0] / rates[i][1], rates[i][1], i) for i in ids
                      if i != first and i in rates and rates[i][1] >= MIN_RUNS]
        worst = max(candidates, key=lambda c: (c[0], c[1], [-ord(ch) for ch in c[2]]), default=None)
        chosen.append({"category": prefix, "first": first, "first_rate": rates.get(first),
                       "worst": worst[2] if worst else None, "worst_rate": rates.get(worst[2]) if worst else None})
    return chosen


def write_manifest(ids: list[str]) -> Path:
    lines = {json.loads(line)["id"]: line for line in (ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl").read_text(
        encoding="utf-8").splitlines() if line.strip()}
    path = ROOT / "prompts" / "TARGETED_MANIFEST.jsonl"
    path.write_bytes("".join(lines[i] + "\n" for i in ids).encode("utf-8"))
    return path


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--write"]
    archive = Path(args[0]) if args else ROOT.parent / "PDLt-Catalogue-Archive"
    rows = select(archive)
    for row in rows:
        print(json.dumps(row))
    ids = [p for row in rows for p in (row["first"], row["worst"]) if p]
    print(json.dumps({"prompts": ids, "count": len(ids)}))
    if "--write" in sys.argv[1:]:
        print(f"written: {write_manifest(ids)}")
