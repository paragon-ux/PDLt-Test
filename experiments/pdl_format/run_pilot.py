#!/usr/bin/env python3
"""Run the PDL-versus-natural-language pilot (ledger L97, plan: experiments/pdl_format/PLAN.md).

    py -3.11 experiments/pdl_format/run_pilot.py --canary          # Task 1, repeat 1, both arms
    py -3.11 experiments/pdl_format/run_pilot.py                   # every remaining full session
    py -3.11 experiments/pdl_format/run_pilot.py --replays         # the 12 frozen-artifact executions

Every session runs the confirmed route. A trunk drafts the prompt and the plan, confirming the
prompt, and stops at the plan review; the trunk is kept as the frozen artifact pair. Each
execution copies the trunk and confirms the plan, so the first execution and the replays run
EXECUTE from byte-identical confirmed artifacts. Sessions already recorded are skipped, so a
stopped run resumes. The arms differ only in ``--representation`` (representation.py).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for entry in (ROOT, ROOT / "src"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from experiments import runner  # noqa: E402
from experiments.sweep_arm import key_state  # noqa: E402

MODEL = {"model": "openai/gpt-oss-120b", "providers": ["Cerebras"]}
SETTINGS = ("--api-reasoning-effort", "low")  # Tier D1 and repairs at the shipped defaults
TIMEOUT_S = 300  # per invocation: the trunk, and each execution
ARMS = {"P": (), "N": ("--representation", "nl")}
TASKS = {
    "T1": "task-01-usage-reconciliation.md",
    "T2": "task-02-queue-cutover.md",
    "T3": "task-03-incident-postmortem.md",
}
# Paired serial order, fixed before any run (kit preregistration.yaml).
ORDER = [("T1", 1, "PN"), ("T1", 2, "NP"), ("T1", 3, "PN"), ("T2", 1, "NP"), ("T2", 2, "PN"), ("T2", 3, "NP"),
         ("T3", 1, "PN"), ("T3", 2, "NP"), ("T3", 3, "PN")]
REPLAYS = (2, 3)  # extra executions of each task's repeat-1 artifacts, per arm
OUT = ROOT / "catalogue-runs" / "pdl-format-pilot"
# Lines of a task packet that address the experimenter, not the requester (removed by a fixed rule).
_GRADER_LINES = re.compile(r"^(\*\*Task ID:\*\*|\*\*Evaluation:\*\*|## Original request shown to both arms)")
_EXPERIMENT_CLAUSE = "; pass these files to both arms unchanged"


def task_prompt(task: str) -> str:
    """The request sent to the model: the task packet without its experimenter-facing lines, and
    Task 1's three fixture files attached verbatim."""
    text = (HERE / "tasks" / TASKS[task]).read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if not _GRADER_LINES.match(line)]
    prompt = "\n".join(lines).replace(_EXPERIMENT_CLAUSE, "").strip() + "\n"
    if task == "T1":
        fixtures = HERE / "tasks" / "fixtures" / "task-01"
        attached = []
        for name, lang in (("accounts.csv", "csv"), ("pricing.json", "json"), ("events.jsonl", "jsonl")):
            body = (fixtures / name).read_text(encoding="utf-8").rstrip("\n")
            attached.append(f"`fixtures/task-01/{name}`:\n\n```{lang}\n{body}\n```")
        prompt += "\n### Attached files\n\n" + "\n\n".join(attached) + "\n"
    return prompt


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def provenance() -> dict:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
    files = sorted(p for p in HERE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    return {"commit": head, "dirty": bool(dirty.strip()),
            "hashes": {p.relative_to(ROOT).as_posix(): sha256(p) for p in files},
            "model": MODEL, "settings": list(SETTINGS), "timeout_s": TIMEOUT_S, "arms": {k: list(v) for k, v in ARMS.items()}}


def spec(arm: str) -> runner.ArmSpec:
    return runner.ArmSpec(f"pdl-format-{arm}", "protocol", worktree=ROOT, args=ARMS[arm])


def record(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def run_trunk(task: str, repeat: int, arm: str, prompt_file: Path) -> dict:
    """Draft and confirm the prompt, draft the plan, stop at the plan review: the frozen artifacts."""
    out = OUT / "sessions" / f"{task}-{arm}-r{repeat}" / "trunk"
    if (out / "trunk.json").is_file():
        return json.loads((out / "trunk.json").read_text(encoding="utf-8"))
    if out.exists():
        shutil.rmtree(out)
    run = runner.run_cli(spec(arm), MODEL, out, prompt_file=prompt_file, restore=None, stdin=runner.TRUNK_STDIN,
                         extra_args=SETTINGS, timeout=TIMEOUT_S)
    stage = runner.controller_stage(out / "session")
    result = {"task": task, "repeat": repeat, "arm": arm, "exit_code": run["exit_code"], "timed_out": run["timed_out"],
              "harness_fault": run["harness_fault"], "elapsed_s": run["elapsed_s"], "stage": stage,
              "at_plan_review": run["exit_code"] == 2 and stage == "PLAN_REVIEW"}
    record(out / "trunk.json", result)
    return result


def run_execution(task: str, repeat: int, arm: str, number: int) -> dict:
    """Copy the frozen trunk and confirm the plan: one EXECUTE from the confirmed artifacts."""
    base = OUT / "sessions" / f"{task}-{arm}-r{repeat}"
    out = base / f"exec{number}"
    if (out / "execution.json").is_file():
        return json.loads((out / "execution.json").read_text(encoding="utf-8"))
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(base / "trunk", out)
    workspace = next((out / "session").glob("W-*"))
    run = runner.run_cli(spec(arm), MODEL, out, prompt_file=None, restore=workspace, stdin=runner.FORCE_CONFIRM,
                         extra_args=SETTINGS, timeout=TIMEOUT_S)
    result = {"task": task, "repeat": repeat, "arm": arm, "execution": number, "replay": number > 1,
              "exit_code": run["exit_code"], "timed_out": run["timed_out"], "harness_fault": run["harness_fault"],
              "elapsed_s": run["elapsed_s"], "stage": runner.controller_stage(out / "session")}
    record(out / "execution.json", result)
    return result


def session(task: str, repeat: int, arm: str, prompt_file: Path) -> list[dict]:
    trunk = run_trunk(task, repeat, arm, prompt_file)
    print(f"  {task} r{repeat} {arm} trunk: exit {trunk['exit_code']} stage {trunk['stage']} ({trunk['elapsed_s']} s)",
          flush=True)
    if not trunk["at_plan_review"]:
        return [trunk]  # the session ended before execution; that is its outcome
    execution = run_execution(task, repeat, arm, 1)
    print(f"  {task} r{repeat} {arm} exec1: exit {execution['exit_code']} ({execution['elapsed_s']} s)", flush=True)
    return [trunk, execution]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--canary", action="store_true", help="Task 1, repeat 1, both arms only")
    group.add_argument("--replays", action="store_true", help="the frozen-artifact executions (after all sessions)")
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args(argv)
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is not set")
        return 2
    meta = provenance()
    if meta["dirty"] and not args.allow_dirty:
        print("refusing to run from a dirty tree (commit first, or --allow-dirty)")
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    prompts = OUT / "prompts"
    prompts.mkdir(exist_ok=True)
    for task in TASKS:
        (prompts / f"{task}.txt").write_text(task_prompt(task), encoding="utf-8")
    phase = "canary" if args.canary else "replays" if args.replays else "sessions"
    before = key_state()
    started = time.time()
    rows: list[dict] = []
    if args.replays:
        for task in TASKS:
            for arm in "PN":
                trunk = run_trunk(task, 1, arm, prompts / f"{task}.txt")
                if not trunk["at_plan_review"]:
                    continue
                for number in REPLAYS:
                    rows.append(run_execution(task, 1, arm, number))
                    print(f"  {task} r1 {arm} exec{number}: exit {rows[-1]['exit_code']} ({rows[-1]['elapsed_s']} s)",
                          flush=True)
    else:
        for task, repeat, order in (ORDER[:1] if args.canary else ORDER):
            for arm in order:
                rows += session(task, repeat, arm, prompts / f"{task}.txt")
    time.sleep(20)  # let the key's usage counter settle
    after = key_state()
    record(OUT / f"{phase}-{time.strftime('%Y%m%d-%H%M%S')}.json",
           {"phase": phase, "provenance": meta, "wall_s": round(time.time() - started, 1),
            "cost_usd": round(after["usage"] - before["usage"], 4), "remaining_after": after["remaining"],
            "rows": rows})
    print(json.dumps({"phase": phase, "cost_usd": round(after["usage"] - before["usage"], 4),
                      "remaining_after": after["remaining"], "wall_s": round(time.time() - started, 1)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
