#!/usr/bin/env python3
"""
PDLt Prompt Catalogue - Automated Test Runner
==============================================

Executes every prompt in CATALOGUE_MANIFEST.jsonl through the live pdlt REPL
in non-interactive mode. Each prompt gets exactly ONE attempt. No retries,
no do-overs, no cherry-picking.

Usage:
    python run_catalogue.py [--model MODEL] [--reasoning EFFORT] [--category CAT] [--dry-run]

Outputs:
    catalogue-runs/<timestamp>/
        +-- RUN_META.json           # Run configuration and environment
        +-- SCOREBOARD.json         # Aggregate results
        +-- SCOREBOARD.md           # Human-readable scoreboard
        +-- results/
            +-- 01-01_schur_triples_n15/
            |   +-- transcript.txt  # Full pdlt session output
            |   +-- stderr.txt      # Stderr capture
            |   +-- result.json     # Structured result (exit code, timing, verdict)
            +-- ...
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PDLT_TEST_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PDLT_TEST_ROOT / "prompts"
MANIFEST_PATH = PROMPTS_DIR / "CATALOGUE_MANIFEST.jsonl"
RUNS_DIR = Path(__file__).resolve().parent
TIMEOUT_PER_PROMPT = 300
EXIT_SUCCESS = 0
EXIT_UNCONFIRMED = 2
EXIT_WAITING_INPUT = 3


def load_manifest(category_filter=None):
    entries = []
    cats = set()
    if category_filter:
        for c in str(category_filter).split(","):
            c = c.strip()
            if c:
                cats.add(c)
                if c.isdigit():
                    cats.add(f"{int(c):02d}")

    with open(MANIFEST_PATH, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if cats:
                entry_cat = entry.get("category", "")
                entry_id_prefix = entry["id"][:2]
                entry_num_str = str(int(entry_id_prefix)) if entry_id_prefix.isdigit() else ""
                if not (entry_cat in cats or entry_id_prefix in cats or entry_num_str in cats):
                    continue
            entries.append(entry)
    return entries


def run_single_prompt(entry, run_dir, model, reasoning_effort, timeout):
    prompt_id = entry["id"]
    prompt_file = PROMPTS_DIR / entry["file"]
    safe_name = f"{prompt_id}_{prompt_file.stem}"
    result_dir = run_dir / "results" / safe_name
    result_dir.mkdir(parents=True, exist_ok=True)

    session_id = f"catalogue-{prompt_id}-{int(time.time())}"
    transcript_path = result_dir / "transcript.txt"
    session_dir = result_dir / "session"
    session_dir.mkdir(exist_ok=True)

    repl_input = "/confirm\n" * 5

    cmd = [
        sys.executable, "-m", "pdl_taskmaster.host.cli",
        "--non-interactive",
        "--exit-on-close",
        "--dev",
        "--new-session",
        "--session-id", session_id,
        "--transcript", str(transcript_path),
        "--workdir", str(session_dir),
        "--model", model,
        "--api-reasoning-effort", reasoning_effort,
        "--api-structured-output",
        "--prompt-file", str(prompt_file),
    ]

    start_time = time.monotonic()
    start_ts = datetime.now(timezone.utc).isoformat()

    try:
        proc = subprocess.run(
            cmd,
            input=repl_input,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=str(PDLT_TEST_ROOT),
            env={**os.environ, "PYTHONPATH": str(
                PDLT_TEST_ROOT.parent / "PDL-Standard-REPL-Harness" / "src"
            ), "PYTHONIOENCODING": "utf-8"},
        )
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
        timed_out = False
    except subprocess.TimeoutExpired as e:
        exit_code = -1
        stdout = e.stdout or ""
        stderr = (e.stderr or "") + f"\n[RUNNER] TIMEOUT after {timeout}s"
        timed_out = True

    elapsed = time.monotonic() - start_time

    if stdout:
        (result_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
    if stderr:
        (result_dir / "stderr.txt").write_text(stderr, encoding="utf-8")

    if timed_out:
        verdict = "TIMEOUT"
    elif exit_code == EXIT_SUCCESS:
        verdict = "CLOSED_SUCCESS"
    elif exit_code == EXIT_WAITING_INPUT:
        verdict = "WAITING_INPUT"
    elif exit_code == EXIT_UNCONFIRMED:
        verdict = "UNCONFIRMED_GATE"
    else:
        verdict = f"EXIT_{exit_code}"

    ground_truth_check = None
    if entry.get("solution_file") and entry["ground_truth_status"] == "verified":
        sol_path = PROMPTS_DIR / entry["solution_file"]
        if sol_path.exists():
            solution = json.loads(sol_path.read_text(encoding="utf-8-sig"))
            ground_truth_check = {
                "solution_file": entry["solution_file"],
                "expected_behavior": solution.get("expected_behavior"),
                "polarity": solution.get("polarity"),
                "note": "Ground truth available - manual or automated comparison required post-run",
            }

    result = {
        "id": prompt_id,
        "category": entry["category"],
        "file": entry["file"],
        "difficulty": entry["difficulty"],
        "expected_routing": entry["expected_routing"],
        "expected_stage": entry["expected_stage"],
        "ground_truth_status": entry["ground_truth_status"],
        "verdict": verdict,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "elapsed_seconds": round(elapsed, 2),
        "start_time": start_ts,
        "session_id": session_id,
        "transcript_file": str(transcript_path.relative_to(run_dir)),
        "ground_truth_check": ground_truth_check,
        "pdl_rules_stressed": entry.get("pdl_rules_stressed", []),
        "tags": entry.get("tags", []),
        "regression_ref": entry.get("regression_ref"),
    }

    (result_dir / "result.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


def is_prompt_pass(r):
    exp = r.get("expected_stage", "CLOSED_SUCCESS")
    if exp == "WAITING_INPUT":
        return r.get("verdict") in {"WAITING_INPUT", "CLOSED_SUCCESS"}
    return r.get("verdict") == exp


def generate_scoreboard(results, run_dir, run_meta):
    total = len(results)
    by_verdict = {}
    by_category = {}
    by_difficulty = {}
    regressions_hit = []

    for r in results:
        v = r["verdict"]
        by_verdict[v] = by_verdict.get(v, 0) + 1

        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = {"total": 0, "pass": 0, "fail": 0}
        by_category[cat]["total"] += 1
        is_pass = is_prompt_pass(r)
        if is_pass:
            by_category[cat]["pass"] += 1
        else:
            by_category[cat]["fail"] += 1

        d = r["difficulty"]
        if d not in by_difficulty:
            by_difficulty[d] = {"total": 0, "pass": 0}
        by_difficulty[d]["total"] += 1
        if is_pass:
            by_difficulty[d]["pass"] += 1

        if r.get("regression_ref") and not is_pass:
            regressions_hit.append({
                "id": r["id"], "regression_ref": r["regression_ref"], "verdict": v,
            })

    passed = sum(1 for r in results if is_prompt_pass(r))
    pass_rate = (passed / total * 100) if total > 0 else 0
    total_time = sum(r["elapsed_seconds"] for r in results)

    scoreboard = {
        "run_id": run_meta["run_id"],
        "timestamp": run_meta["start_time"],
        "model": run_meta["model"],
        "reasoning_effort": run_meta["reasoning_effort"],
        "total_prompts": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate_pct": round(pass_rate, 1),
        "total_elapsed_seconds": round(total_time, 1),
        "by_verdict": by_verdict,
        "by_category": by_category,
        "by_difficulty": by_difficulty,
        "regressions_hit": regressions_hit,
        "failures": [
            {"id": r["id"], "category": r["category"], "verdict": r["verdict"],
             "elapsed": r["elapsed_seconds"]}
            for r in results if not is_prompt_pass(r)
        ],
    }

    (run_dir / "SCOREBOARD.json").write_text(
        json.dumps(scoreboard, indent=2), encoding="utf-8"
    )

    # Markdown scoreboard
    lines = [
        f"# PDLt Catalogue Run - {scoreboard['run_id']}",
        "",
        f"**Model:** `{scoreboard['model']}`  ",
        f"**Reasoning Effort:** `{scoreboard['reasoning_effort']}`  ",
        f"**Timestamp:** {scoreboard['timestamp']}  ",
        f"**Total Time:** {scoreboard['total_elapsed_seconds']:.1f}s  ",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Prompts | {scoreboard['total_prompts']} |",
        f"| Passed | {scoreboard['passed']} |",
        f"| Failed | {scoreboard['failed']} |",
        f"| **Pass Rate** | **{scoreboard['pass_rate_pct']}%** |",
        "",
        "---",
        "",
        "## By Category",
        "",
        "| Category | Total | Pass | Fail | Rate |",
        "|----------|-------|------|------|------|",
    ]
    for cat in sorted(scoreboard["by_category"].keys()):
        c = scoreboard["by_category"][cat]
        rate = (c["pass"] / c["total"] * 100) if c["total"] > 0 else 0
        lines.append(f"| {cat} | {c['total']} | {c['pass']} | {c['fail']} | {rate:.0f}% |")

    lines += ["", "---", "", "## By Difficulty", "",
              "| Difficulty | Total | Pass | Rate |",
              "|-----------|-------|------|------|"]
    for d in ["easy", "medium", "hard", "adversarial"]:
        if d in scoreboard["by_difficulty"]:
            dd = scoreboard["by_difficulty"][d]
            rate = (dd["pass"] / dd["total"] * 100) if dd["total"] > 0 else 0
            lines.append(f"| {d} | {dd['total']} | {dd['pass']} | {rate:.0f}% |")

    if scoreboard["failures"]:
        lines += ["", "---", "", "## Failures", "",
                  "| ID | Category | Verdict | Time (s) |",
                  "|----|----------|---------|----------|"]
        for f in scoreboard["failures"]:
            lines.append(f"| {f['id']} | {f['category']} | {f['verdict']} | {f['elapsed']:.1f} |")

    if scoreboard["regressions_hit"]:
        lines += ["", "---", "", "## KNOWN REGRESSIONS HIT", "",
                  "| ID | Regression Ref | Verdict |",
                  "|----|---------------|---------|"]
        for r in scoreboard["regressions_hit"]:
            lines.append(f"| {r['id']} | {r['regression_ref']} | {r['verdict']} |")

    lines += ["", "---", "", "## Per-Prompt Results", "",
              "| ID | Category | Difficulty | Verdict | Time (s) |",
              "|----|----------|-----------|---------|----------|"]
    for r in results:
        icon = "PASS" if is_prompt_pass(r) else "FAIL"
        lines.append(
            f"| {icon} {r['id']} | {r['category']} | {r['difficulty']} "
            f"| {r['verdict']} | {r['elapsed_seconds']:.1f} |"
        )

    (run_dir / "SCOREBOARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return scoreboard


def main():
    parser = argparse.ArgumentParser(
        description="PDLt Prompt Catalogue Test Runner - no retries, no shortcuts"
    )
    parser.add_argument("--model", default="openai/gpt-oss-120b",
                        help="Model to test (default: openai/gpt-oss-120b)")
    parser.add_argument("--reasoning", default="low",
                        choices=["low", "medium", "high"],
                        help="Reasoning effort level (default: low)")
    parser.add_argument("--category", default=None,
                        help="Run only a specific category (e.g. 'combinatorial_search' or '01,13,14')")
    parser.add_argument("--categories", dest="category",
                        help="Alias for --category with comma-separated list")
    parser.add_argument("--fail-fast", "--stop-on-failure", action="store_true",
                        help="Stop execution immediately upon any prompt failure")
    parser.add_argument("--prompt-id", default=None,
                        help="Run only a specific prompt by ID (e.g. '01-02')")
    parser.add_argument("--dry-run", action="store_true",
                        help="List prompts that would be run without executing")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_PER_PROMPT,
                        help=f"Per-prompt timeout in seconds (default: {TIMEOUT_PER_PROMPT})")
    args = parser.parse_args()

    entries = load_manifest(category_filter=args.category)
    if args.prompt_id:
        entries = [e for e in entries if e["id"] == args.prompt_id]

    if not entries:
        print("No prompts match the filter. Exiting.")
        sys.exit(1)

    print(f"PDLt Prompt Catalogue Test Runner")
    print(f"{'=' * 50}")
    print(f"Model:      {args.model}")
    print(f"Reasoning:  {args.reasoning}")
    print(f"Prompts:    {len(entries)}")
    print(f"Timeout:    {args.timeout}s per prompt")
    print()

    if args.dry_run:
        print("DRY RUN - prompts that would be executed:")
        for e in entries:
            gt = "VERIFIED" if e["ground_truth_status"] == "verified" else "       "
            print(f"  {gt} {e['id']:6s} [{e['difficulty']:11s}] {e['file']}")
        n_verified = sum(1 for e in entries if e["ground_truth_status"] == "verified")
        print(f"\nVERIFIED = verified ground truth ({n_verified} prompts)")
        sys.exit(0)

    run_id = datetime.now().strftime("run-%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / run_id
    (run_dir / "results").mkdir(parents=True)

    run_meta = {
        "run_id": run_id,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "reasoning_effort": args.reasoning,
        "category_filter": args.category,
        "prompt_id_filter": args.prompt_id,
        "total_prompts": len(entries),
        "timeout_per_prompt": args.timeout,
        "pdlt_test_root": str(PDLT_TEST_ROOT),
        "rules": {
            "retries_allowed": 0,
            "do_overs_allowed": False,
            "non_interactive": True,
            "exit_on_close": True,
            "dev_mode": True,
            "structured_output": True,
        },
    }
    (run_dir / "RUN_META.json").write_text(
        json.dumps(run_meta, indent=2), encoding="utf-8"
    )

    results = []
    for i, entry in enumerate(entries, 1):
        prompt_id = entry["id"]
        print(f"[{i:3d}/{len(entries)}] {prompt_id:6s} {entry['category']:30s} ", end="", flush=True)
        result = run_single_prompt(entry, run_dir, args.model, args.reasoning, args.timeout)
        results.append(result)
        icon = "PASS" if is_prompt_pass(result) else "FAIL"
        print(f"{icon} {result['verdict']:20s} ({result['elapsed_seconds']:.1f}s)")

        if args.fail_fast and not is_prompt_pass(result):
            print(f"\n[FAIL-FAST] Stopping execution immediately after failure on {prompt_id} ({result['verdict']}).")
            break

    print()
    print(f"{'=' * 50}")
    scoreboard = generate_scoreboard(results, run_dir, run_meta)
    print(f"Pass Rate: {scoreboard['pass_rate_pct']}% "
          f"({scoreboard['passed']}/{scoreboard['total_prompts']})")
    print(f"Total Time: {scoreboard['total_elapsed_seconds']:.1f}s")
    print(f"Results: {run_dir}")
    print(f"Scoreboard: {run_dir / 'SCOREBOARD.md'}")

    if scoreboard["regressions_hit"]:
        print(f"\nKNOWN REGRESSIONS HIT: {len(scoreboard['regressions_hit'])}")
        for r in scoreboard["regressions_hit"]:
            print(f"    {r['id']} ({r['regression_ref']}): {r['verdict']}")

    exit_code = 1 if (scoreboard["regressions_hit"] or (args.fail_fast and scoreboard.get("failed", 0) > 0)) else 0
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

