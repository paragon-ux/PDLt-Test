"""Measure the problem-class classifier with System 1 calls only.

Runs ProblemClassRecipe through the System 1 client the engine uses (the one
ApiWorker builds) over the catalogue prompts and any extra questions, and prints
per question the verdict, confidence, margin, entropy, whether it passed the
confidence gate, and the resulting requires_verified_execution (VERIFIED only
when the gate passed, as in the engine). No System 2 call, no session, no sandbox:
a cheap way to compare classifier wordings before a full catalogue run.

    python scripts/probe_problem_class.py
    python scripts/probe_problem_class.py --category 01
    python scripts/probe_problem_class.py --ids 01-02,01-03 --text "What is 2 + 2?" --file question.txt
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from pdl_taskmaster.providers.sys1.recipes.problem_class import ProblemClassRecipe  # noqa: E402

PROMPTS_DIR = ROOT / "prompts"


def build_sys1_client(api_key_env: str) -> Any:
    """The System 1 client exactly as the engine gets it: ApiWorker builds it
    (host/app.py passes ``worker.sys1_client`` to the engine)."""
    from pdl_taskmaster.providers.api_worker import ApiWorker

    return ApiWorker(repo_root=ROOT, api_key_env=api_key_env).sys1_client


def catalogue_questions(category: str | None, ids: str | None) -> list[dict[str, Any]]:
    """Catalogue prompts, filtered as run_catalogue.py filters --category, then by --ids."""
    from run_catalogue import load_manifest

    wanted = {i.strip() for i in (ids or "").split(",") if i.strip()}
    questions = []
    for entry in load_manifest(category_filter=category):
        if wanted and entry["id"] not in wanted:
            continue
        text = (PROMPTS_DIR / entry["file"]).read_text(encoding="utf-8-sig").strip()
        questions.append({"id": entry["id"], "text": text, "expected": entry.get("expected_routing")})
    return questions


def extra_questions(texts: list[str], files: list[str]) -> list[dict[str, Any]]:
    questions = [{"id": f"text-{n}", "text": t.strip(), "expected": None} for n, t in enumerate(texts, 1)]
    for path in files:
        questions.append({"id": Path(path).name, "text": Path(path).read_text(encoding="utf-8-sig").strip(),
                          "expected": None})
    return questions


def classify(client: Any, text: str) -> dict[str, Any]:
    """One ProblemClassRecipe decision, routed the way the engine routes it."""
    recipe = ProblemClassRecipe()
    body, duration_ms = client.call(recipe.build_request({"request": text}))
    result = recipe.parse_response(body, duration_ms=duration_ms)
    return {
        "verdict": result.verdict,
        "confidence": result.confidence,
        "margin": result.margin,
        "entropy": result.entropy,
        "passed_gating": result.passed_gating,
        "requires_verified_execution": result.passed_gating and result.verdict == "VERIFIED_EXECUTION",
        "duration_ms": duration_ms,
    }


def summarize(records: list[dict[str, Any]]) -> list[str]:
    ok = [r for r in records if "error" not in r]
    verified = [r for r in ok if r["verdict"] == "VERIFIED_EXECUTION"]
    lines = [
        f"questions: {len(records)}  answered: {len(ok)}  errors: {len(records) - len(ok)}",
        f"VERIFIED verdicts: {len(verified)}  STANDARD verdicts: {len(ok) - len(verified)}",
        f"passed gating: {sum(r['passed_gating'] for r in ok)}  "
        f"requires_verified_execution: {sum(r['requires_verified_execution'] for r in ok)}  "
        f"VERIFIED below the gate: {sum(not r['passed_gating'] for r in verified)}",
    ]
    for label, group in (("VERIFIED", verified), ("all", ok)):
        if group:
            values = [r["confidence"] for r in group]
            lines.append(f"confidence ({label}): min {min(values):.2f}  median {statistics.median(values):.2f}  "
                         f"max {max(values):.2f}")
    expected = [r for r in ok if r.get("expected")]
    if expected:
        agree = [r for r in expected if (r["requires_verified_execution"]
                                         == (r["expected"] == "VERIFIED_EXECUTION"))]
        lines.append(f"routing matches manifest expected_routing: {len(agree)}/{len(expected)}")
        lines += [f"  differs: {r['id']} expected {r['expected']}, routed "
                  f"{'VERIFIED' if r['requires_verified_execution'] else 'STANDARD'}"
                  for r in expected if r not in agree]
    return lines


def main(argv: list[str] | None = None, client: Any = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--category", default=None,
                        help="catalogue categories as run_catalogue.py takes them, e.g. 01 or 01,13")
    parser.add_argument("--ids", default=None, help="comma-separated prompt ids, e.g. 01-02,01-03")
    parser.add_argument("--text", action="append", default=[], help="an extra question (repeatable)")
    parser.add_argument("--file", action="append", default=[], help="a file holding an extra question (repeatable)")
    parser.add_argument("--no-catalogue", action="store_true", help="classify only --text and --file questions")
    parser.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    args = parser.parse_args(argv)

    if client is None:
        client = build_sys1_client(args.api_key_env)
    if not getattr(client, "is_configured", False):
        print(f"System 1 is not configured: set SYS1_API_KEY or {args.api_key_env} "
              "(SYS1_ENDPOINT and SYS1_MODEL are optional).", file=sys.stderr)
        return 2

    questions = [] if args.no_catalogue else catalogue_questions(args.category, args.ids)
    questions += extra_questions(args.text, args.file)
    if not questions:
        print("No questions selected.", file=sys.stderr)
        return 2

    print(f"System 1 model: {getattr(client, 'model', '?')}  floor: {ProblemClassRecipe().min_confidence}")
    print(f"{'id':16s} {'verdict':20s} {'conf':>5s} {'margin':>6s} {'entropy':>7s} {'gated':>5s} "
          f"{'verified':>8s}  expected")
    records = []
    for question in questions:
        record: dict[str, Any] = {"id": question["id"], "expected": question["expected"]}
        try:
            record.update(classify(client, question["text"]))
            line = (f"{record['verdict']:20s} {record['confidence']:5.2f} {record['margin']:6.2f} "
                    f"{record['entropy']:7.2f} {str(record['passed_gating']):>5s} "
                    f"{str(record['requires_verified_execution']):>8s}  {question['expected'] or ''}")
        except Exception as exc:  # reported, never hidden
            record["error"] = f"{type(exc).__name__}: {exc}"
            line = f"ERROR {record['error'][:200]}"
        records.append(record)
        print(f"{question['id'][:16]:16s} {line}", flush=True)
    print()
    for line in summarize(records):
        print(line)
    return 1 if any("error" in r for r in records) else 0


if __name__ == "__main__":
    sys.exit(main())
