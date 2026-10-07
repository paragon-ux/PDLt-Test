"""The catalogue baseline: past runs regraded with today's graders, read-only (T9).

`run_catalogue.py --regrade` rewrites a run's files. This instead reads each
finished run and leaves it unchanged. It grades every result with the current
graders (FA2: MANUAL is pending, never a pass; hidden tests for the coding
prompts) and writes `experiments/baseline/BASELINE.json` and `BASELINE.md`.

For every run, it reports the old and new outcome per prompt, and the pass rate
over the prompts a machine grader decides (PASS or FAIL). The baseline only says
what the shipped protocol achieved on these runs, graded the same way the gate
will grade. It decides nothing.

    python -m experiments.baseline catalogue-runs/run-20261002-012111 [more run dirs]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "baseline"


def _manifest() -> dict[str, dict[str, Any]]:
    text = (ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl").read_text(encoding="utf-8-sig")
    return {e["id"]: e for e in (json.loads(l) for l in text.splitlines() if l.strip())}


def regrade(run_dir: Path) -> dict[str, Any]:
    import graders
    import run_catalogue

    manifest = _manifest()
    meta_path = run_dir / "RUN_META.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
    rows = []
    for result_file in sorted((run_dir / "results").glob("*/result.json")):
        result = json.loads(result_file.read_text(encoding="utf-8"))
        entry = manifest.get(result["id"])
        if entry is None:
            continue
        old = (result.get("ground_truth_grade") or {}).get("grade")
        if result.get("timed_out"):
            new = {"grade": graders.FAIL if entry.get("ground_truth_status") == "verified" else graders.NA,
                   "reason": "timeout"}
        else:
            new = graders.grade(entry, result_file.parent, ROOT / "prompts")
        stage_ok = run_catalogue.stage_pass(result)
        rows.append({"id": result["id"], "category": entry["category"], "verdict": result.get("verdict"),
                     "stage_pass": stage_ok, "old_grade": old, "new_grade": new["grade"],
                     "reason": str(new.get("reason", ""))[:300],
                     "grader": "hidden_tests" if entry.get("hidden_tests") else
                               ("machine" if entry.get("ground_truth_status") == "verified" else "none")})
    decided = [r for r in rows if r["new_grade"] in (graders.PASS, graders.FAIL)]
    passed = [r for r in decided if r["new_grade"] == graders.PASS and r["stage_pass"]]
    return {"run": run_dir.name, "model": meta.get("model"), "effort": meta.get("reasoning_effort"),
            "prompts": len(rows), "decided": len(decided), "passed": len(passed),
            "decided_pass_rate": round(len(passed) / len(decided), 4) if decided else None,
            "pending": sum(1 for r in rows if r["new_grade"] == graders.MANUAL),
            "changed": [r for r in rows if r["old_grade"] != r["new_grade"]], "rows": rows}


def markdown(runs: list[dict[str, Any]]) -> str:
    lines = ["# Catalogue baseline (regraded, read-only)", "",
             "Past runs graded with the current graders: FA2, hidden tests for the coding prompts. "
             "Pass = the run reached its expected stage and the grader returned PASS; "
             "the rate is over prompts a grader decides (PASS or FAIL).", "",
             "| Run | Model | Effort | Prompts | Decided | Passed | Decided pass rate | Pending (MANUAL) |",
             "|---|---|---|---|---|---|---|---|"]
    for r in runs:
        rate = f"{100 * r['decided_pass_rate']:.1f}%" if r["decided_pass_rate"] is not None else "n/a"
        lines.append(f"| {r['run']} | {r['model']} | {r['effort']} | {r['prompts']} | {r['decided']} | {r['passed']} | "
                     f"{rate} | {r['pending']} |")
    for r in runs:
        lines += ["", f"## {r['run']}: grades that changed", "", "| Prompt | Old | New | Reason |", "|---|---|---|---|"]
        for c in r["changed"]:
            lines.append(f"| {c['id']} | {c['old_grade']} | {c['new_grade']} | {c['reason'][:120].replace('|', '/')} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    runs = [regrade(Path(a)) for a in argv]
    OUT.mkdir(exist_ok=True)
    (OUT / "BASELINE.json").write_text(json.dumps(runs, indent=2) + "\n", encoding="utf-8", newline="\n")
    (OUT / "BASELINE.md").write_text(markdown(runs), encoding="utf-8", newline="\n")
    for r in runs:
        print(f"{r['run']}: {r['passed']}/{r['decided']} decided ({r['decided_pass_rate']}), {r['pending']} pending, "
              f"{len(r['changed'])} grades changed")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main(sys.argv[1:]))
