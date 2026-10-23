"""Pre-merge catalogue check (AGENTS.md): run_catalogue.py --fail-fast with the L127 baseline's settings (shipped
defaults, openai/gpt-oss-120b), category by category; after a stop, the category's remaining prompts run one by one.
Every outcome is compared with the L127 baseline's. Spend is checked between invocations.

    py -3.11 experiments/premerge_catalogue.py REPO OUT_JSON
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2])
ARCHIVE = REPO.parent / "PDLt-Catalogue-Archive"
BASELINE = ARCHIVE / "run-20261017-171943-unconfirmed-tier-d1"
MIN_REMAINING = 0.08  # stop and ask before the key runs dry

sys.path[:0] = [str(REPO), str(REPO / "experiments")]
import matched_study  # noqa: E402
import run_catalogue  # noqa: E402

manifest = [json.loads(l) for l in (REPO / "prompts" / "CATALOGUE_MANIFEST.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
categories = []
for entry in manifest:
    if entry["category"] not in categories:
        categories.append(entry["category"])


def results_of(run_dir):
    out = {}
    for rd in sorted((run_dir / "results").glob("*")):
        f = rd / "result.json"
        if f.is_file():
            r = json.loads(f.read_text(encoding="utf-8"))
            out[rd.name[:5]] = r
    return out


baseline = {pid: run_catalogue.outcome_class(r) for pid, r in results_of(BASELINE).items()}
state = json.loads(OUT.read_text(encoding="utf-8")) if OUT.is_file() else {"outcomes": {}, "runs": [], "stops": []}


def invoke(args):
    before = {p.name for p in ARCHIVE.glob("run-*")}
    cmd = [sys.executable, "run_catalogue.py", "--model", "openai/gpt-oss-120b", "--fail-fast", *args]
    code = subprocess.call(cmd, cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    new = sorted({p.name for p in ARCHIVE.glob("run-*")} - before)
    run_dir = ARCHIVE / new[-1] if new else None
    state["runs"].append({"args": args, "exit": code, "run": new[-1] if new else None})
    found = results_of(run_dir) if run_dir else {}
    for pid, r in found.items():
        state["outcomes"][pid] = {"outcome": run_catalogue.outcome_class(r), "baseline": baseline.get(pid),
                                  "verdict": r.get("verdict"), "run": run_dir.name}
    OUT.write_text(json.dumps(state, indent=1), encoding="utf-8")
    return found


def budget_ok():
    remaining = matched_study.key_state().get("limit_remaining")
    if remaining is not None and remaining < MIN_REMAINING:
        state["stopped_for_budget"] = remaining
        OUT.write_text(json.dumps(state, indent=1), encoding="utf-8")
        print(json.dumps({"stopped_for_budget": remaining}))
        return False
    return True


for category in categories:
    ids = [e["id"] for e in manifest if e["category"] == category]
    if all(pid in state["outcomes"] for pid in ids):
        continue
    if not budget_ok():
        sys.exit(2)
    pending = [pid for pid in ids if pid not in state["outcomes"]]
    if pending == ids:
        invoke(["--category", category])
    for pid in [p for p in ids if p not in state["outcomes"]]:
        if not budget_ok():
            sys.exit(2)
        state["stops"].append({"category": category, "continued_at": pid})
        invoke(["--prompt-id", pid])

regressions = sorted(pid for pid, o in state["outcomes"].items()
                     if o["outcome"] in ("FAIL", "HELD") and o["baseline"] not in ("FAIL", "HELD"))
improved = sorted(pid for pid, o in state["outcomes"].items()
                  if o["baseline"] in ("FAIL", "HELD") and o["outcome"] == "PASS")
counts = {}
for o in state["outcomes"].values():
    counts[o["outcome"]] = counts.get(o["outcome"], 0) + 1
base_counts = {}
for v in baseline.values():
    base_counts[v] = base_counts.get(v, 0) + 1
state["summary"] = {"counts": counts, "baseline_counts": base_counts, "regressions": regressions,
                    "improved": improved, "prompts": len(state["outcomes"])}
OUT.write_text(json.dumps(state, indent=1), encoding="utf-8")
print(json.dumps(state["summary"], indent=1))
