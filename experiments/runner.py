"""The acceptance-gate runner (design §9).

Subcommands, all of which read one JSON config (``experiments/gate_config.example.json``):
- ``plan``: the schedule, unit counts and the request estimate, with no calls.
- ``run``: executes the schedule, sequential and in the foreground. Resumable from
  the ledger. ``--smoke`` runs one block of a trivial prompt that is in no set, to
  check the tooling end to end.
- ``export``: the blind adjudication sheet (``experiments.adjudicate``).
- ``report``: decisions and estimates per model (``experiments.analysis``).

**Launch the runner from P_new's worktree.** The plain-call arms run in-process
and must mirror P_new's EXECUTE (§4). The protocol arms run as subprocesses of
the harness CLI, each in its own worktree with that worktree's ``src`` on
``PYTHONPATH`` and its contracts as ``--candidate-repo``.

**A branched arm** runs its trunk with one piped ``/confirm`` (for the prompt).
The trunk stops at plan review (exit 2, expected). Each branch resumes a copy of
the trunk's workspace with ``--restore`` and its own flags. Since FA5,
``--restore`` keeps System 1's routing (§3.2).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import graders
import run_catalogue
from experiments import adjudicate, analysis, grading
from experiments.prompt_set import LOCK_PATH
from experiments.schedule import MAX_BLOCK_RERUNS, Block, Ledger, build_schedule

ROOT = Path(__file__).resolve().parents[1]
FORCE_CONFIRM = "/confirm\n" * 5
TRUNK_STDIN = "/confirm\n"  # confirms the prompt; the trunk then stops at plan review
SMOKE_ITEM = "SMOKE-01"
SMOKE_TEXT = "Compute the product of 7 and 8."


@dataclass(frozen=True)
class ArmSpec:
    name: str
    kind: str  # "control", "protocol" or "branched"
    effort: str | None = None
    worktree: Path | None = None
    args: tuple[str, ...] = ()
    branches: dict[str, tuple[str, ...]] | None = None  # branched: branch name -> extra args (the scoring branch is the arm's name)

    def units(self, block: Block) -> list[tuple[str, str | None]]:
        if self.kind == "branched":
            return [(self.name, b) for b in block.branches.get(self.name, tuple(self.branches or ()))]
        return [(self.name, None)]


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    config["arms"] = {
        name: ArmSpec(name, spec["kind"], spec.get("effort"),
                      Path(spec["worktree"]).resolve() if spec.get("worktree") else None,
                      tuple(spec.get("args", ())),
                      {b: tuple(a) for b, a in spec.get("branches", {}).items()} or None)
        for name, spec in config["arms"].items()
    }
    return config


def gate_items(strata: list[str]) -> list[dict[str, Any]]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    return [i for i in lock["items"] if i["stratum"] in strata]


def expected_stage(item_id: str) -> str:
    manifest = {e["id"]: e for e in map(json.loads, filter(str.strip, (ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl")
                                                          .read_text(encoding="utf-8-sig").splitlines()))}
    return manifest[item_id]["expected_stage"] if item_id in manifest else "CLOSED_SUCCESS"


# --------------------------------------------------------------------------- scoring

def to_score(stage_ok: bool, grade: str) -> int | None:
    """1 pass, 0 fail, None pending adjudication (MANUAL or N/A). A missed stage is a fail."""
    if not stage_ok or grade in (graders.FAIL, "ERROR"):
        return 0
    return 1 if grade == graders.PASS else None


EXIT_VERDICT = {0: "CLOSED_SUCCESS", 1: "CLOSED_CANCELLED", 2: "UNCONFIRMED_GATE", 3: "WAITING_INPUT",
                4: "HARNESS_ERROR"}


def classify_protocol_failure(run: dict[str, Any]) -> str | None:
    """None: a model outcome to score. "outage": void the block (§9.5); a harness
    fault (memory, hang, runner timeout) is re-run the same way. A deadline, a
    malformed reply and the output cap are model outcomes even when the CLI exits 4."""
    exit_code, stderr = run["exit_code"], run["stderr"]
    if run["timed_out"] or run.get("harness_fault"):
        return "outage"
    if exit_code != 4:
        return None
    record = run_catalogue.harness_error_record(stderr) or {}
    category = str(record.get("category", "")).upper()
    message = str(record.get("message", "")).lower()
    if "deadline" in message or "timed out twice" in message or category in (
            "OUTPUT_MALFORMED", "OUTPUT_LIMIT_REACHED", "CALL_DEADLINE"):
        return None
    status = record.get("status")
    if category == "PROVIDER_REJECTED_REQUEST" and status == 400 and "schema" in message:
        return None  # a provider rejecting this arm's request shape is the arm's outcome, not an outage
    return "outage"


def score_protocol(item: grading.Item, run: dict[str, Any], result_dir: Path) -> dict[str, Any]:
    verdict = EXIT_VERDICT.get(run["exit_code"], f"EXIT_{run['exit_code']}")
    stage_ok = run_catalogue.stage_pass({"expected_stage": expected_stage(item.id), "verdict": verdict})
    kind, text, bypassed = grading.published(result_dir)
    final = grading.grade_text(item, kind, text)
    first = grading.first_attempt(result_dir)
    first_grade = grading.grade_text(item, first["kind"], first["text"]) if first["status"] == "reply" else \
        {"grade": graders.FAIL, "reason": first["status"]}
    primary = to_score(stage_ok, final["grade"])
    stopped = grading.headless_stop(result_dir)
    usage = run_catalogue.call_accounting(result_dir)
    return {
        "cost": {"calls": usage["total"], "input_tokens": sum(usage["input_tokens"].values()),
                 "output_tokens": sum(usage["output_tokens"].values())},
        "verdict": verdict, "exit_code": run["exit_code"], "published_kind": kind, "bypassed": bypassed,
        "grade": final, "first_attempt": {"status": first["status"], "grade": first_grade},
        "headless_stop": stopped, "system1": grading.system1_verdicts(result_dir),
        "scores": {"primary": primary, "p_first": to_score(True, first_grade["grade"]),
                   "headless": 0 if stopped else primary,
                   "reached_execute": first["status"] != "not_reached"},
    }


# --------------------------------------------------------------------------- running units

def run_cli(spec: ArmSpec, model: dict[str, Any], out: Path, *, prompt_file: Path | None, restore: Path | None,
            stdin: str, extra_args: tuple[str, ...], timeout: float) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    session_dir = out / "session"
    session_dir.mkdir(exist_ok=True)
    cmd = [sys.executable, "-m", "pdl_taskmaster.host.cli", "--non-interactive", "--exit-on-close", "--dev",
           "--new-session", "--session-id", f"gate-{uuid.uuid4().hex[:10]}", "--transcript", str(out / "transcript.txt"),
           "--workspace-root", str(session_dir), "--workdir", str(session_dir),
           "--candidate-repo", str(spec.worktree), "--model", model["model"],
           "--api-providers", ",".join(model["providers"]), "--api-structured-output",
           *spec.args, *extra_args]
    cmd += ["--restore", str(restore)] if restore is not None else ["--prompt-file", str(prompt_file)]
    env = {**os.environ, "PYTHONPATH": str(spec.worktree / "src"), "PYTHONIOENCODING": "utf-8"}
    started = time.monotonic()
    exit_code, timed_out, containment = run_catalogue.run_with_deadline(
        cmd, stdin, timeout, out / "stdout.txt", out / "stderr.txt", cwd=str(spec.worktree), env=env)
    stderr = (out / "stderr.txt").read_text(encoding="utf-8", errors="replace") if (out / "stderr.txt").is_file() else ""
    (out / "command.json").write_text(json.dumps({"cmd": cmd, "stdin": stdin}, indent=2), encoding="utf-8")
    return {"exit_code": exit_code, "timed_out": timed_out, "stderr": stderr,
            "harness_fault": run_catalogue.harness_fault(containment, stderr),
            "elapsed_s": round(time.monotonic() - started, 2)}


def controller_stage(session_dir: Path) -> str | None:
    states = sorted(Path(session_dir).rglob("controller-state.json"))
    if not states:
        return None
    return json.loads(states[-1].read_text(encoding="utf-8")).get("stage")


def run_branched(spec: ArmSpec, model, item, out: Path, prompt_file: Path, branch_order, timeout) \
        -> list[tuple[str, dict[str, Any] | None, Path, str | None]]:
    """[(branch, run, result_dir, failure)] for each branch, sharing one trunk."""
    trunk_dir = out / "trunk"
    trunk = run_cli(spec, model, trunk_dir, prompt_file=prompt_file, restore=None, stdin=TRUNK_STDIN,
                    extra_args=(), timeout=timeout)
    failure = classify_protocol_failure(trunk)
    at_plan_review = trunk["exit_code"] == 2 and controller_stage(trunk_dir / "session") == "PLAN_REVIEW"
    if failure or not at_plan_review:
        # The trunk ended before execution (a refusal, a failure, an outage): every branch shares that outcome.
        return [(b, trunk, trunk_dir, failure) for b in branch_order]
    results = []
    for branch in branch_order:
        branch_dir = out / branch
        if branch_dir.exists():
            shutil.rmtree(branch_dir)
        shutil.copytree(trunk_dir, branch_dir)
        workspace = next((branch_dir / "session").glob("W-*"))
        run = run_cli(spec, model, branch_dir, prompt_file=None, restore=workspace, stdin=FORCE_CONFIRM,
                      extra_args=spec.branches.get(branch, ()), timeout=timeout)
        results.append((branch, run, branch_dir, classify_protocol_failure(run)))
    return results


def run_block(config, block: Block, items: dict[str, grading.Item], ledger: Ledger, controls_by_model) -> bool:
    """Run a block's unfinished units. False when an outage voided the block."""
    model = next(m for m in config["models"] if m["name"] == block.model)
    item = items[block.item_id]
    attempt = ledger.attempt(block.block_id)
    base = Path(config["out_dir"]) / block.model / block.item_id / f"r{block.rep}" / f"a{attempt}"
    prompt_file = base / "prompt.txt"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(item.prompt_text.strip() + "\n", encoding="utf-8")
    done = ledger.done_units(block.block_id)
    stratum = config["_strata"].get(block.item_id, "SMOKE")
    common = {"block_id": block.block_id, "attempt": attempt, "model": block.model, "item_id": block.item_id,
              "stratum": stratum, "rep": block.rep,
              # Generated items from one template are one analysis unit (design §8.3, LEDGER L19).
              "cluster": config.get("_clusters", {}).get(block.item_id, block.item_id)}
    snapshot = None
    for arm in block.arms:
        spec: ArmSpec = config["arms"][arm]
        units = [u for u in spec.units(block) if u not in done]
        if not units:
            continue
        if spec.kind == "control":
            controls = controls_by_model[block.model]
            if snapshot is None:
                from experiments.controls import system1_snapshot

                snapshot = system1_snapshot(item.prompt_text, controls.worker.sys1_client, controls.sandbox)
            result = controls.run(arm, item.prompt_text.strip(), effort=spec.effort, tier=snapshot["tier"],
                                  verified=snapshot["verified"])
            if result.status == "outage":
                ledger.void_block(block.block_id, f"{arm}: {result.error}")
                return False
            grade = grading.grade_text(item, result.kind, result.text) if result.status == "reply" else \
                {"grade": graders.FAIL, "reason": result.status}
            unit_dir = base / arm
            unit_dir.mkdir(parents=True, exist_ok=True)
            (unit_dir / "reply.json").write_text(json.dumps({**result.as_dict(), "text": result.text}, indent=2,
                                                            ensure_ascii=False), encoding="utf-8")
            usage = result.usage or {}
            ledger.append({**common, "arm": arm, "branch": None, "status": "done", "control": result.as_dict(),
                           "system1_snapshot": snapshot, "grade": grade, "elapsed_s": result.latency_s,
                           "cost": {"calls": 1, "input_tokens": usage.get("input_tokens") or 0,
                                    "output_tokens": usage.get("output_tokens") or 0},
                           "scores": {"primary": to_score(True, grade["grade"])}})
            continue
        if spec.kind == "branched":
            for branch, run, result_dir, failure in run_branched(spec, model, item, base / arm, prompt_file,
                                                                 [b for a, b in units], config["prompt_timeout_s"]):
                if failure == "outage":
                    ledger.void_block(block.block_id, f"{arm}/{branch}: outage")
                    return False
                ledger.append({**common, "arm": branch, "unit_arm": arm, "branch": branch, "status": "done",
                               "elapsed_s": run["elapsed_s"], **score_protocol(item, run, result_dir)})
            continue
        run = run_cli(spec, model, base / arm, prompt_file=prompt_file, restore=None, stdin=FORCE_CONFIRM,
                      extra_args=(), timeout=config["prompt_timeout_s"])
        if classify_protocol_failure(run) == "outage":
            ledger.void_block(block.block_id, f"{arm}: outage")
            return False
        ledger.append({**common, "arm": arm, "branch": None, "status": "done", "elapsed_s": run["elapsed_s"],
                       **score_protocol(item, run, base / arm)})
    return True


# --------------------------------------------------------------------------- commands

def _schedule(config, smoke: bool) -> tuple[list[Block], dict[str, grading.Item]]:
    if smoke:
        items = {SMOKE_ITEM: grading.Item(SMOKE_ITEM, "smoke", SMOKE_TEXT,
                                          lambda corpus: (graders.PASS, "56") if "56" in corpus else
                                          (graders.FAIL, "56 not found"))}
        config["_strata"] = {}
        ids = [SMOKE_ITEM]
    else:
        locked = gate_items(config["strata"])
        config["_strata"] = {i["id"]: i["stratum"] for i in locked}
        config["_clusters"] = {i["id"]: f"{i['set']}-{i['family']}" for i in locked if i.get("family")}
        catalogue = {**grading.catalogue_items(), **grading.generated_items("gate")}
        items = {i["id"]: catalogue[i["id"]] for i in locked}
        ids = [i["id"] for i in locked]
    branches = {name: list(spec.branches) for name, spec in config["arms"].items() if spec.kind == "branched"}
    blocks = build_schedule([m["name"] for m in config["models"]], ids, reps=1 if smoke else config["reps"],
                            arms=list(config["arms"]), branches=branches, seed=config["seed"])
    return blocks, items


def cmd_plan(config, args) -> int:
    blocks, _ = _schedule(config, args.smoke)
    units = sum(len(config["arms"][a].units(b)) for b in blocks for a in b.arms)
    print(f"{len(blocks)} blocks, {units} arm runs, models: {', '.join(m['name'] for m in config['models'])}")
    for block in blocks[: args.show]:
        print(f"  {block.block_id}: {' > '.join(block.arms)}"
              + "".join(f"  [{a}: {' > '.join(b)}]" for a, b in block.branches.items()))
    return 0


def cmd_run(config, args) -> int:
    from experiments.controls import Controls

    out = Path(config["out_dir"]) / ("smoke" if args.smoke else "")
    config["out_dir"] = str(out)
    ledger = Ledger(out / "ledger.jsonl")
    blocks, items = _schedule(config, args.smoke)
    controls_by_model = {m["name"]: Controls(ROOT, model=m["model"], providers=m["providers"],
                                             sampling=m.get("sampling"),
                                             trace_path=out / m["name"] / "controls-call-trace.jsonl")
                         for m in config["models"]}
    ran = 0
    try:
        for block in blocks:
            needed = {u for a in block.arms for u in config["arms"][a].units(block)}
            if needed <= ledger.done_units(block.block_id):
                continue
            if args.max_blocks is not None and ran >= args.max_blocks:
                break
            for _ in range(MAX_BLOCK_RERUNS + 1):
                if run_block(config, block, items, ledger, controls_by_model):
                    break
            else:
                ledger.append({"block_id": block.block_id, "attempt": ledger.attempt(block.block_id), "arm": "*",
                               "branch": None, "status": "dropped", "reason": "outage after every re-run"})
            ran += 1
            print(f"[{ran}] {block.block_id} done", flush=True)
    finally:
        for controls in controls_by_model.values():
            controls.close()
    return 0


def cmd_export(config, args) -> int:
    rows = Ledger(Path(config["out_dir"]) / "ledger.jsonl").results()
    chosen = adjudicate.queue(rows, seed=args.seed)
    texts = []
    for row in chosen:
        text = (row.get("control") or {}).get("text")
        texts.append({"model": row["model"], "item_id": row["item_id"], "rep": row["rep"], "arm": row["arm"],
                      "text": text if text is not None else _published_text(config, row)})
    sheet, key = grading.export_adjudication(texts, Path(config["out_dir"]) / "adjudication", seed=args.seed)
    print(f"{len(texts)} rows to adjudicate: {sheet}\nkey (keep it from the adjudicators): {key}")
    return 0


def _published_text(config, row) -> str | None:
    base = Path(config["out_dir"]) / row["model"] / row["item_id"] / f"r{row['rep']}" / f"a{row['attempt']}"
    for candidate in (base / row["arm"], *base.glob(f"*/{row['arm']}")):
        if candidate.is_dir():
            reply = candidate / "reply.json"
            if reply.is_file():
                return json.loads(reply.read_text(encoding="utf-8")).get("text")
            return grading.published(candidate)[1]
    return None


def cmd_report(config, args) -> int:
    rows = Ledger(Path(config["out_dir"]) / "ledger.jsonl").results()
    verdicts = adjudicate.read_verdicts(Path(args.sheet), Path(args.key)) if args.sheet else {}
    rows = adjudicate.apply(rows, verdicts)
    facts = json.loads(Path(args.mechanism).read_text(encoding="utf-8")) if args.mechanism else {}
    report: dict[str, Any] = {}
    for model in sorted({r["model"] for r in rows}):
        entry: dict[str, Any] = {}
        try:
            entry["gate"] = analysis.gate_decision(rows, model, mechanism_checks=facts.get("G3", {}))
        except analysis.PendingAdjudication as exc:
            entry["gate"] = f"pending adjudication: {exc}"
        if any(r["arm"] == "P_unc" and r["model"] == model for r in rows):
            try:
                entry["ultrafast"] = analysis.ultrafast_decision(rows, model, mechanism_checks=facts.get("U3", {}))
            except analysis.PendingAdjudication as exc:
                entry["ultrafast"] = f"pending adjudication: {exc}"
        secondary = {}
        for a, b in (("C0", "C1"), ("C1", "C2"), ("C2", "C3"), ("EXEC_HI", "P_new"), ("DE", "P_new"),
                     ("DE", "EXEC_HI")):
            try:
                secondary[f"{a} - {b}"] = analysis.compare(rows, model, a, b, score="audited").as_dict()
            except analysis.PendingAdjudication as exc:
                secondary[f"{a} - {b}"] = f"pending: {exc}"
        entry["secondary"] = secondary
        report[model] = entry
    print(json.dumps(report, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "run", "export", "report"):
        p = sub.add_parser(name)
        p.add_argument("--config", required=True, type=Path)
        if name in ("plan", "run"):
            p.add_argument("--smoke", action="store_true", help="one block of a trivial prompt that is in no set")
        if name == "plan":
            p.add_argument("--show", type=int, default=5)
        if name == "run":
            p.add_argument("--max-blocks", type=int, default=None)
        if name == "export":
            p.add_argument("--seed", type=int, required=True)
        if name == "report":
            p.add_argument("--sheet")
            p.add_argument("--key")
            p.add_argument("--mechanism")
    args = parser.parse_args(argv)
    config = load_config(args.config)
    return {"plan": cmd_plan, "run": cmd_run, "export": cmd_export, "report": cmd_report}[args.command](config, args)


if __name__ == "__main__":
    sys.exit(main())
