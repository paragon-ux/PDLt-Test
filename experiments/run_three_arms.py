#!/usr/bin/env python3
"""
Sequential Three-Arm Parity Runner:
1. Arm 1: Unconfirmed (ultrafast)
2. Arm 2: Confirmed (multi-stage)
3. Arm 3: Confirmed + DRAFT-EXECUTE

Runs all three arms sequentially over the stratified 16-prompt catalogue sample
to avoid OpenRouter provider-queue contention.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
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
        "label": "Arm 3: Confirmed + DRAFT-EXECUTE (--route confirmed --draft-execute)",
        "args": ["--route", "confirmed", "--draft-execute"],
    },
]


def run_arm(arm_info):
    print("\n" + "=" * 70)
    print(f"STARTING {arm_info['label']}")
    print("=" * 70 + "\n", flush=True)

    cmd = [
        sys.executable,
        "run_catalogue.py",
        "--model", MODEL,
        "--prompt-id", PROMPTS,
        "--reasoning", REASONING,
        "--timeout", TIMEOUT,
        *arm_info["args"],
    ]

    t0 = time.time()
    proc = subprocess.run(cmd, cwd=str(ROOT))
    elapsed = time.time() - t0
    print(f"\n[DONE] {arm_info['label']} in {elapsed:.1f}s (exit {proc.returncode})\n", flush=True)
    return proc.returncode


def summarize_results():
    runs_dir = ROOT / "catalogue-runs"
    # Find newest run directories for each arm
    scoreboard_data = {}
    for arm in ARMS:
        name = arm["name"]
        matching = sorted(runs_dir.glob(f"run-*-{name}"), key=lambda p: p.stat().st_mtime, reverse=True)
        if matching:
            sb_path = matching[0] / "SCOREBOARD.json"
            if sb_path.exists():
                try:
                    scoreboard_data[name] = json.loads(sb_path.read_text(encoding="utf-8"))
                except Exception as e:
                    print(f"Could not load {sb_path}: {e}")

    print("\n" + "#" * 70)
    print("THREE-ARM PARITY COMPARISON MATRIX")
    print("#" * 70)
    header = f"{'Prompt':<8} | {'Category':<24} | {'Arm 1 (Unconfirmed)':<18} | {'Arm 2 (Confirmed)':<18} | {'Arm 3 (Conf+Draft)':<18}"
    print(header)
    print("-" * len(header))

    prompt_ids = PROMPTS.split(",")
    for pid in prompt_ids:
        row = [f"{pid:<8}"]
        cat = None
        for arm in ARMS:
            sb = scoreboard_data.get(arm["name"])
            if sb and "prompts" in sb and pid in sb["prompts"]:
                pinfo = sb["prompts"][pid]
                if cat is None:
                    cat = pinfo.get("category", "")
                v = pinfo.get("verdict", "N/A")
                gt = pinfo.get("ground_truth_grade", {}).get("grade", "N/A")
                t = pinfo.get("elapsed_seconds", 0)
                cell = f"{v[:10]} ({gt}) {t:.0f}s"
            else:
                cell = "NOT_RUN"
            row.append(cell)
        cat_str = (cat or "")[:24]
        print(f"{row[0]} | {cat_str:<24} | {row[1]:<18} | {row[2]:<18} | {row[3]:<18}")

    print("-" * len(header))
    summary_row = f"{'TOTALS':<8} | {'Pass Rate / Elapsed':<24}"
    for arm in ARMS:
        sb = scoreboard_data.get(arm["name"])
        if sb:
            rate = sb.get("pass_rate_pct", 0)
            elapsed = sb.get("total_time_seconds", 0)
            calls = sb.get("model_calls", {}).get("total", 0)
            summary_row += f" | {rate:.1f}% ({calls}c, {elapsed:.0f}s)"
        else:
            summary_row += " | N/A"
    print(summary_row)
    print("#" * 70 + "\n")


def main():
    for arm in ARMS:
        run_arm(arm)
    summarize_results()


if __name__ == "__main__":
    main()
