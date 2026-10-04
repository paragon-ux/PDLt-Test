"""PLAN-02 plan-gate check against the live System 1 judge.

For every case in prompts/16_logic_and_reasoning/plan_gate_cases.json, the
confirmed Prompt Pseudocode and each supplied response plan go to the same
PlanAdvancementRecipe decision the engine makes at plan review. A reasoning plan
must not be rejected; a copied, paraphrased or mechanically expanded plan must be.

    python run_plan_gate.py                 # every case once
    python run_plan_gate.py --repeat 3      # each decision three times (stability)
    python run_plan_gate.py --case 16-01

Writes catalogue-runs/plan-gate-<ts>/results.json and SUMMARY.md. Exit 0 when every
decision matches its expectation, 1 otherwise, 4 when System 1 is not configured.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from pdl_taskmaster.providers.sys1.client import Sys1Client  # noqa: E402
from pdl_taskmaster.providers.sys1.recipes.plan_advancement import PlanAdvancementRecipe  # noqa: E402

CASES = ROOT / "prompts" / "16_logic_and_reasoning" / "plan_gate_cases.json"


def matches(expect: str, verdict: str | None) -> bool:
    """The engine rejects only a confident RESTATES; anything else lets the plan through."""
    return verdict == "RESTATES" if expect == "reject" else verdict != "RESTATES"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--case", default=None, help="only this case id (e.g. 16-01)")
    args = parser.parse_args()

    client = Sys1Client()
    if not client.is_configured:
        print("System 1 is not configured (set OPENROUTER_API_KEY or SYS1_API_KEY)", file=sys.stderr)
        return 4
    data = json.loads(CASES.read_text(encoding="utf-8"))
    recipe = PlanAdvancementRecipe()
    rows: list[dict] = []
    decisions = [(case["id"], kind, case["prompt"], plan, data["expect"][kind])
                 for case in data["cases"] for kind, plan in case["plans"].items()]
    decisions += [(case["id"], "extra", case["prompt"], case["plan"], case["expect"])
                  for case in data.get("extra_cases", [])]
    for (case_id, kind, prompt, plan, expect), attempt in (
        (decision, attempt) for decision in decisions for attempt in range(1, args.repeat + 1)
    ):
        if args.case and case_id != args.case:
            continue
        started = time.perf_counter()
        try:
            body, duration_ms = client.call(recipe.build_request({"confirmed_prompt": prompt, "response_plan": plan}))
            wire = recipe.map_to_wire(recipe.parse_response(body, duration_ms=duration_ms))
            verdict, failed, checks, error = wire["verdict"], wire["failed_checks"], wire["checks"], None
        except Exception as exc:  # recorded, counted as a mismatch
            verdict, failed, checks, error = None, [], {}, f"{type(exc).__name__}: {exc}"
        ok = error is None and matches(expect, verdict)
        rows.append({"id": case_id, "plan": kind, "attempt": attempt, "expect": expect,
                     "verdict": verdict, "failed_checks": failed, "checks": checks, "ok": ok,
                     "error": error, "ms": round((time.perf_counter() - started) * 1000)})
        print(f"{case_id} {kind:<11} expect {expect:<6} -> {str(verdict):<20} "
              f"{'ok' if ok else 'MISMATCH'}  {','.join(failed)}", flush=True)

    out = ROOT / "catalogue-runs" / f"plan-gate-{datetime.now():%Y%m%d-%H%M%S}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps({"model": client.model, "rows": rows}, indent=2) + "\n",
                                      encoding="utf-8")
    mismatches = [r for r in rows if not r["ok"]]
    lines = [f"# Plan gate ({client.model})", "",
             f"{len(rows) - len(mismatches)}/{len(rows)} decisions match their expectation.", "",
             "| case | plan | expect | verdict | failed checks |", "|---|---|---|---|---|"]
    lines += [f"| {r['id']} | {r['plan']} | {r['expect']} | {r['verdict']} | {', '.join(r['failed_checks'])} |"
              for r in rows]
    (out / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n{len(rows) - len(mismatches)}/{len(rows)} match; results: {out}")
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
