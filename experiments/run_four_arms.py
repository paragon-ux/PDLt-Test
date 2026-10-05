#!/usr/bin/env python3
"""
Sequential Four-Arm Parity Runner:
1. Arm 1: Unconfirmed (ultrafast, 2-call)
2. Arm 2: Confirmed (multi-stage)
3. Arm 3: Confirmed + DRAFT-EXECUTE (multi-stage + brief)
4. Arm 4: Unconfirmed + DRAFT-EXECUTE (lean 3-call)
"""

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = "01-01,02-01,03-01,04-01,05-01,06-01,07-01,08-01,09-01,10-01,11-01,12-01,13-01,14-01,15-01,16-01"
MODEL = "openai/gpt-oss-120b"
TIMEOUT = "90"
REASONING = "low"

ARMS = [
    {
        "name": "unconfirmed",
        "label": "Arm 1: Unconfirmed (--route unconfirmed)",
        "args": ["--route", "unconfirmed"],
    },
    {
        "name": "confirmed",
        "label": "Arm 2: Confirmed (--route confirmed)",
        "args": ["--route", "confirmed"],
    },
    {
        "name": "confirmed-draft-execute",
        "label": "Arm 3: Confirmed + DRAFT-EXECUTE (--route confirmed --draft-execute --tier-d1)",
        "args": ["--route", "confirmed", "--draft-execute", "--tier-d1"],
    },
    {
        "name": "unconfirmed-draft-execute",
        "label": "Arm 4: Unconfirmed + DRAFT-EXECUTE (--route unconfirmed --draft-execute --tier-d1)",
        "args": ["--route", "unconfirmed", "--draft-execute", "--tier-d1"],
    },
]


def run_arm(arm_info, repeat: int = 1, prompts: str = PROMPTS):
    print("\n" + "=" * 70)
    print(f"STARTING {arm_info['label']}" + (f" (repeat x{repeat})" if repeat > 1 else "") + f" [prompts: {prompts}]")
    print("=" * 70 + "\n", flush=True)

    cmd = [
        sys.executable,
        "run_catalogue.py",
        "--model", MODEL,
        "--prompt-id", prompts,
        "--reasoning", REASONING,
        "--timeout", TIMEOUT,
        *arm_info["args"],
    ]
    if repeat > 1:
        cmd += ["--repeat", str(repeat)]

    t0 = time.time()
    proc = subprocess.run(cmd, cwd=str(ROOT))
    elapsed = time.time() - t0
    print(f"\n[DONE] {arm_info['label']} in {elapsed:.1f}s (exit {proc.returncode})\n", flush=True)
    return proc.returncode


def summarize_results(target_prompts: str | None = None):
    runs_dir = ROOT / "catalogue-runs"
    prompt_ids = (target_prompts or PROMPTS).split(",")
    # Find newest run directories for each arm
    arm_runs = {}
    for candidate in sorted(runs_dir.glob("run-*"), key=lambda p: p.stat().st_mtime, reverse=True):
        if not candidate.is_dir():
            continue
        sb_path = candidate / "SCOREBOARD.json"
        if not sb_path.exists():
            continue
        try:
            data = json.loads(sb_path.read_text(encoding="utf-8"))
            if target_prompts:
                if data.get("total_prompts") != len(prompt_ids):
                    continue
            else:
                if data.get("total_prompts") != 16:
                    continue
        except Exception:
            continue

        cname = candidate.name
        parts = cname.split("-", 3)
        tag = parts[3] if len(parts) >= 4 else ""
        if tag.startswith("unconfirmed-draft-execute"):
            arm_name = "unconfirmed-draft-execute"
        elif tag.startswith("confirmed-draft-execute"):
            arm_name = "confirmed-draft-execute"
        elif tag.startswith("unconfirmed"):
            arm_name = "unconfirmed"
        elif tag.startswith("confirmed"):
            arm_name = "confirmed"
        else:
            continue

        if arm_name not in arm_runs:
            arm_runs[arm_name] = candidate

    # Load results per prompt
    results_map = {}  # arm_name -> pid -> result_dict
    scoreboards = {}
    for arm in ARMS:
        name = arm["name"]
        rdir = arm_runs.get(name)
        if not rdir:
            continue
        sb_path = rdir / "SCOREBOARD.json"
        scoreboards[name] = json.loads(sb_path.read_text(encoding="utf-8"))
        results_map[name] = {}
        for res_file in (rdir / "results").glob("*/result.json"):
            try:
                res_data = json.loads(res_file.read_text(encoding="utf-8"))
                pid = res_data.get("id")
                if pid:
                    results_map[name][pid] = res_data
            except Exception:
                pass

    print("\n" + "#" * 90)
    print("FOUR-ARM PARITY COMPARISON MATRIX")
    print("#" * 90)
    header = f"{'Prompt':<6} | {'Arm 1 (Unconf)':<18} | {'Arm 2 (Conf)':<18} | {'Arm 3 (Conf+Draft)':<18} | {'Arm 4 (Unconf+Draft)':<18}"
    print(header)
    print("-" * len(header))

    for pid in prompt_ids:
        row = [f"{pid:<6}"]
        for arm in ARMS:
            res = results_map.get(arm["name"], {}).get(pid)
            if res:
                v = res.get("verdict", "N/A")
                gt = res.get("ground_truth_grade", {}).get("grade", "N/A")
                t = res.get("elapsed_seconds", 0)
                cell = f"{v[:10]} ({gt}) {t:.0f}s"
            else:
                cell = "NOT_RUN"
            row.append(cell)
        print(f"{row[0]} | {row[1]:<18} | {row[2]:<18} | {row[3]:<18} | {row[4]:<18}")

    print("-" * len(header))
    # Counted from each arm's results, never from its scoreboard's "passed": scoreboards
    # written before L49d (2026-10-05) counted an ungraded prompt as a pass.
    sys.path.insert(0, str(ROOT))
    import run_catalogue

    for arm in ARMS:
        rows = list(results_map.get(arm["name"], {}).values())
        sb = scoreboards.get(arm["name"]) or {}
        if rows:
            counts = run_catalogue.outcome_counts(rows)
            calls = sb.get("model_calls", {}).get("total", 0)
            elapsed = sb.get("total_elapsed_seconds", 0)
            print(f"{arm['label']}: {run_catalogue.format_counts(counts)} ({calls} calls, {elapsed:.0f}s)")
        else:
            print(f"{arm['label']}: not run")
    print("#" * 90)
    print("*(pass: the expected stage and a grader PASS; ungraded and held results are never passes)*\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Sequential Four-Arm Parity Runner")
    parser.add_argument("--summary-only", action="store_true", help="Print summary matrix from newest runs")
    parser.add_argument("--arms", default="1,2,3,4", help="Comma-separated list of arms to run (e.g. '3,4' or '1,2,3,4')")
    parser.add_argument("--arm4-only", action="store_true", help="Run only Arm 4")
    parser.add_argument("--arm3-only", action="store_true", help="Run only Arm 3")
    parser.add_argument("--prompts", default=None, help="Comma-separated list of prompts to run (default: all 16)")
    parser.add_argument("--repeat", type=int, default=1, help="Number of repeats per prompt")
    args = parser.parse_args()

    active_prompts = args.prompts or PROMPTS

    if args.summary_only:
        summarize_results(target_prompts=args.prompts)
        return

    if args.arm3_only:
        run_arm(ARMS[2], repeat=args.repeat, prompts=active_prompts)
        summarize_results(target_prompts=args.prompts)
        return

    if args.arm4_only:
        run_arm(ARMS[3], repeat=args.repeat, prompts=active_prompts)
        summarize_results(target_prompts=args.prompts)
        return

    target_arm_indices = [int(x.strip()) - 1 for x in args.arms.split(",") if x.strip()]
    for idx in target_arm_indices:
        if 0 <= idx < len(ARMS):
            run_arm(ARMS[idx], repeat=args.repeat, prompts=active_prompts)
    summarize_results(target_prompts=args.prompts)


if __name__ == "__main__":
    main()
