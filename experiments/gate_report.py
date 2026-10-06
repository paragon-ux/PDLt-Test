"""Live-gate report over catalogue run folders (GOAL T0.7b; TARGET_ARCHITECTURE I-11).

Per prompt: verdict, grader grade, outcome class (``run_catalogue.outcome_class``), the
09-xx outcome read from the run record, tokens and cost. Per run: counts under the
current and the old counting, with n and a Wilson interval for the pass rate. A
comparison between two runs prints both intervals and says whether they separate the
runs; a difference whose intervals overlap is labelled anecdotal.

usage:
  python -m experiments.gate_report RUN_DIR [RUN_DIR ...]
  python -m experiments.gate_report RUN_DIR --compare BASE_RUN_DIR
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import run_catalogue  # noqa: E402

# Crusoe's list price for openai/gpt-oss-120b, OpenRouter, 2026-10-05 (LEDGER L64, AD-9).
PRICE_IN_PER_M = 0.05
PRICE_OUT_PER_M = 0.25
ADVERSARIAL = run_catalogue.ADVERSARIAL_CATEGORY
DISPOSITION_EVENT = "RISK_DISPOSITION"
BLOCKED_KINDS = {"BLOCKED_BY_HIGHER_PRIORITY"}


def wilson(passed: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """The Wilson score interval for a pass rate (95% by default)."""
    if n == 0:
        return (0.0, 1.0)
    p = passed / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def adversarial_outcome(result_dir: Path, result: dict[str, Any]) -> str:
    """How a 09-xx run ended, read from its record: refused, contained or held by the
    host's disposition (Phase 2 on); blocked by the semantic read or System 1; held at a
    gate; or proceeded (which the agent then reads for compliance; LEDGER L61)."""
    for events in sorted(result_dir.rglob("events/events.jsonl")):
        for event in _jsonl(events):
            if event.get("event") == DISPOSITION_EVENT or event.get("type") == DISPOSITION_EVENT:
                payload = event.get("payload") or event.get("data") or event
                value = str(payload.get("disposition", "")).lower()
                return {"refuse": "refused", "contain": "contained", "hold": "held",
                        "proceed": "proceeded"}.get(value, value or "proceeded")
    for reply in sorted(result_dir.rglob("0001-bootstrap_analysis/model-response.txt")):
        try:
            data = json.loads(reply.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("outcome", data).get("kind") in BLOCKED_KINDS:
            return "blocked"
    if result.get("verdict") == run_catalogue.HOLD_VERDICT:
        return "held"
    if result.get("routing") == "BLOCKED_BY_HIGHER_PRIORITY" or str(result.get("closure", "")).upper() == "REFUSED":
        return "blocked"
    return "proceeded"


def usage(result_dir: Path) -> dict[str, int]:
    tokens_in = tokens_out = calls = 0
    for path in result_dir.rglob("observations/*.jsonl"):
        for record in _jsonl(path):
            stack: list[Any] = [record]
            while stack:
                item = stack.pop()
                if isinstance(item, dict):
                    found = item.get("usage")
                    if isinstance(found, dict) and "output_tokens" in found:
                        tokens_in += int(found.get("input_tokens") or 0)
                        tokens_out += int(found.get("output_tokens") or 0)
                        calls += 1
                    stack.extend(v for k, v in item.items() if k != "usage")
                elif isinstance(item, list):
                    stack.extend(item)
    return {"calls": calls, "input_tokens": tokens_in, "output_tokens": tokens_out}


def cost(tokens: dict[str, int]) -> float:
    return tokens["input_tokens"] / 1e6 * PRICE_IN_PER_M + tokens["output_tokens"] / 1e6 * PRICE_OUT_PER_M


def read_run(run_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for result_file in sorted((run_dir / "results").glob("*/result.json")):
        result = json.loads(result_file.read_text(encoding="utf-8"))
        tokens = usage(result_file.parent)
        rows.append({
            "id": result.get("id"), "dir": result_file.parent.name, "category": result.get("category"),
            "verdict": result.get("verdict"), "grade": run_catalogue.gt_grade(result),
            "outcome": run_catalogue.outcome_class(result),
            "adversarial": adversarial_outcome(result_file.parent, result)
            if result.get("category") == ADVERSARIAL else None,
            "tokens": tokens, "cost": cost(tokens), "result": result,
        })
    return rows


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = run_catalogue.outcome_counts([r["result"] for r in rows])
    low, high = wilson(counts["pass"], counts["total"])
    return {**counts, "pass_interval": (round(low, 3), round(high, 3)),
            "cost": round(sum(r["cost"] for r in rows), 4),
            "tokens": {k: sum(r["tokens"][k] for r in rows) for k in ("calls", "input_tokens", "output_tokens")}}


def compare(new: dict[str, Any], base: dict[str, Any]) -> str:
    """Two pass rates with n and intervals; separated only when the intervals are disjoint."""
    (a_lo, a_hi), (b_lo, b_hi) = new["pass_interval"], base["pass_interval"]
    separated = a_hi < b_lo or b_hi < a_lo
    return (f"new {new['pass']}/{new['total']} [{a_lo:.2f}, {a_hi:.2f}] vs base {base['pass']}/{base['total']} "
            f"[{b_lo:.2f}, {b_hi:.2f}]: " + ("intervals separate the runs" if separated
                                              else "anecdotal (the intervals overlap)"))


def render(run_dir: Path, rows: list[dict[str, Any]]) -> str:
    lines = [f"== {run_dir.name}"]
    for r in rows:
        extra = f" 09:{r['adversarial']}" if r["adversarial"] else ""
        lines.append(f"  {r['dir']:<34} {r['verdict']:<16} gt={r['grade']:<7} {r['outcome']:<9}{extra} "
                     f"${r['cost']:.4f}")
    s = summary(rows)
    lines.append(f"  {run_catalogue.format_counts(s)}; pass interval {s['pass_interval']}; "
                 f"{s['tokens']['calls']} calls, cost ${s['cost']:.4f}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("runs", nargs="+", type=Path)
    parser.add_argument("--compare", type=Path, default=None, help="a base run folder to compare against")
    args = parser.parse_args(argv)
    total = 0.0
    for run in args.runs:
        rows = read_run(run)
        print(render(run, rows))
        total += summary(rows)["cost"]
        if args.compare:
            print("  " + compare(summary(rows), summary(read_run(args.compare))))
    print(f"total cost ${total:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
