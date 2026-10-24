"""A matched, interleaved live study over frozen implementations (ledger L145).

    python experiments/matched_study.py plan CONFIG [--write-schedule]
    python experiments/matched_study.py preflight CONFIG
    python experiments/matched_study.py run CONFIG [--max-blocks N]
    python experiments/matched_study.py status CONFIG

CONFIG is a JSON file (``experiments/studies/*.json``). Each arm names a worktree, the commit that worktree must be at
(``"self"``: the commit of the checkout running this script) and its ``run_catalogue.py`` arguments; ``shared_args``
go to every arm. One unit is one prompt, one repeat, one arm: ``run_catalogue.py --prompt-id P --repeat 1`` run in the
arm's worktree, so each arm runs its own code (the runner puts its worktree's ``src`` first on the child's path, which
preflight checks), with ``PDLT_CATALOGUE_RUNS`` pointing at the arm's folder under the study's ``out_dir``.

**Schedule** (``experiments/schedule.py``, fixed by the seed): every repetition-1 block, then every repetition-2
block, each pass in its own random prompt order; within a block the arms run in a random order. An arm may name the
repeats it runs in (``"repeats": [1]``); it is left out of the other blocks, and the rest keep their order. ``plan
--write-schedule`` writes the schedule beside the config; ``run`` refuses a schedule that differs from that file.

**Outages** void the whole block, which is re-run (``schedule.MAX_BLOCK_RERUNS`` times at most) and never partly
kept. An outage is a failure that is never a model outcome: the provider unavailable (``harness_error.category``
``PROVIDER_UNAVAILABLE``: HTTP 5xx, 429, transport), a Control call that obtained no generation, or a runner that
wrote no result. Everything else is an outcome and stands: model errors, output limits, timeouts, rejected requests.
A block still failing after its re-runs is kept as it is, flagged, and counted as errors in every analysis.

**Budget.** Before each block the OpenRouter key's ``limit_remaining`` is read; the run stops cleanly (exit 3) when
the remainder is below the reserve plus the block's estimate, or the study's spend would pass its cap. A stopped or
crashed run resumes at the first unfinished block (the ledger is append-only)."""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from catalogue_runs import RUNS_DIR  # noqa: E402
from experiments.schedule import MAX_BLOCK_RERUNS, Block, Ledger, build_schedule  # noqa: E402

KEY_URL = "https://openrouter.ai/api/v1/key"
UNIT_TIMEOUT_S = 1200  # the runner enforces the prompt's own timeout; this only catches a hung runner
OUTAGE_BACKOFF_S = 120
MAX_FAILED_BLOCKS_IN_A_ROW = 3


# ---------------------------------------------------------------------------- config and schedule

def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    problems = []
    for key in ("study", "seed", "repeats", "prompts", "arms", "out_dir"):
        if key not in config:
            problems.append(f"missing {key}")
    for name, arm in (config.get("arms") or {}).items():
        for key in ("worktree", "commit", "args"):
            if key not in arm:
                problems.append(f"arm {name}: missing {key}")
        bad = [r for r in arm.get("repeats", []) if not 1 <= r <= config.get("repeats", 0)]
        if bad:
            problems.append(f"arm {name}: repeats {bad} outside 1..{config.get('repeats')}")
    if len(set(config.get("prompts", []))) != len(config.get("prompts", [])):
        problems.append("a prompt is listed twice")
    if problems:
        raise SystemExit(f"{path}: " + "; ".join(problems))
    config["_path"] = str(Path(path).resolve())
    return config


def items(config: dict[str, Any]) -> list[str]:
    return list(config["prompts"]) + list(config.get("heldout", {}).get("prompts", []))


def schedule(config: dict[str, Any]) -> list[Block]:
    arms = sorted(config["arms"])
    blocks = build_schedule([config["study"]], items(config), reps=config["repeats"], arms=arms, seed=config["seed"])
    kept = []
    for block in blocks:
        order = tuple(a for a in block.arms if block.rep in config["arms"][a].get("repeats", range(1, block.rep + 1)))
        kept.append(dataclasses.replace(block, arms=order))
    return kept


def schedule_json(blocks: list[Block]) -> str:
    return json.dumps([b.as_dict() for b in blocks], indent=1, sort_keys=True) + "\n"


def schedule_path(config: dict[str, Any]) -> Path:
    return Path(config["_path"]).with_suffix(".schedule.json")


def sha256(text: str | bytes) -> str:
    return hashlib.sha256(text.encode("utf-8") if isinstance(text, str) else text).hexdigest()


def out_dir(config: dict[str, Any]) -> Path:
    path = Path(config["out_dir"])
    return path if path.is_absolute() else RUNS_DIR / path


def worktree(config: dict[str, Any], arm: str) -> Path:
    path = Path(config["arms"][arm]["worktree"]).expanduser()
    return path if path.is_absolute() else (Path(config["_path"]).parent / path).resolve()


def unit_command(config: dict[str, Any], arm: str, item: str) -> list[str]:
    command = [sys.executable, "run_catalogue.py", "--prompt-id", item, "--repeat", "1",
               *config.get("shared_args", []), *config["arms"][arm]["args"]]
    heldout = config.get("heldout", {})
    if item in heldout.get("prompts", []):
        command += ["--manifest", heldout["manifest"]]
    return command


def estimate(config: dict[str, Any], blocks: list[Block]) -> dict[str, Any]:
    per_run = (config.get("budget") or {}).get("per_run_usd", {})
    runs = {arm: sum(arm in b.arms for b in blocks) for arm in sorted(config["arms"])}
    cost = {arm: round(n * float(per_run.get(arm, 0.0)), 4) for arm, n in runs.items()}
    return {"runs": runs, "total_runs": sum(runs.values()), "cost_usd": cost,
            "total_cost_usd": round(sum(cost.values()), 2)}


# ---------------------------------------------------------------------------- git, key, preflight

def git(path: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, check=True).stdout.strip()


def expected_commit(config: dict[str, Any], arm: str) -> str:
    commit = config["arms"][arm]["commit"]
    return git(ROOT, "rev-parse", "HEAD") if commit == "self" else git(worktree(config, arm), "rev-parse", commit)


def key_state() -> dict[str, Any]:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    request = urllib.request.Request(KEY_URL, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))["data"]
    return {"usage": float(data.get("usage") or 0.0), "limit": data.get("limit"),
            "limit_remaining": data.get("limit_remaining")}


def preflight(config: dict[str, Any], *, check_key: bool = True) -> list[str]:
    """Every check an arm must pass before any spend; returns the problems (none: ready)."""
    problems: list[str] = []
    stray = sorted(k for k in os.environ if (k.startswith("PDLT_") or k.startswith("SYS1_"))
                   and k != "PDLT_CATALOGUE_RUNS")
    if stray:  # each would change what some arm runs (PDLT_AGENT_TOOLS, PDLT_TIER_D1, PDLT_STANDARDS_PATH, ...)
        problems.append(f"environment variables that change a run are set: {', '.join(stray)}")
    if git(ROOT, "status", "--porcelain"):
        problems.append(f"the driver's checkout {ROOT} has uncommitted changes")
    committed = schedule_path(config)
    if not committed.is_file() or committed.read_text(encoding="utf-8") != schedule_json(schedule(config)):
        problems.append(f"{committed.name} is missing or differs from the schedule the config gives")
    trees: dict[str, Path] = {}
    for arm in sorted(config["arms"]):
        tree = worktree(config, arm)
        trees[arm] = tree
        if not (tree / "run_catalogue.py").is_file():
            problems.append(f"{arm}: {tree} has no run_catalogue.py")
            continue
        if git(tree, "status", "--porcelain"):
            problems.append(f"{arm}: {tree} has uncommitted changes")
        head, want = git(tree, "rev-parse", "HEAD"), expected_commit(config, arm)
        if head != want:
            problems.append(f"{arm}: {tree} is at {head[:10]}, not {want[:10]}")
        env = {**os.environ, "PYTHONPATH": str(tree / "src")}
        found = subprocess.run([sys.executable, "-c", "import pdl_taskmaster; print(pdl_taskmaster.__file__)"],
                               cwd=tree, env=env, capture_output=True, text=True).stdout.strip()
        if not found or not Path(found).resolve().is_relative_to(tree.resolve()):
            problems.append(f"{arm}: the child would import pdl_taskmaster from {found or 'nowhere'}, not {tree}")
        for item in sorted(set(items(config)))[:1] + sorted(set(config.get("heldout", {}).get("prompts", [])))[:1]:
            dry = subprocess.run(unit_command(config, arm, item) + ["--dry-run"], cwd=tree, capture_output=True,
                                 text=True, env={**os.environ, "PDLT_CATALOGUE_RUNS": str(out_dir(config) / arm)})
            if dry.returncode != 0 or item not in dry.stdout:
                problems.append(f"{arm}: the runner refused its arguments for {item}: {dry.stderr.strip()[-300:]}")
    for relative in config.get("same_files", []):
        digests = {}
        for arm, tree in trees.items():
            path = tree / relative
            digests[arm] = sha256(path.read_bytes()) if path.is_file() else None
        if len(set(digests.values())) != 1:
            problems.append(f"{relative} differs between arms: " + ", ".join(f"{a} {d and d[:10]}"
                                                                             for a, d in digests.items()))
    if check_key:
        try:
            state = key_state()
            need = remaining_estimate(config)
            if state["limit_remaining"] is not None and state["limit_remaining"] < need:
                problems.append(f"the key has ${state['limit_remaining']:.2f} left; the study's remaining estimate "
                                f"is ${need:.2f}")
        except Exception as exc:  # noqa: BLE001  (no key, no network: not ready)
            problems.append(f"the key could not be read ({exc.__class__.__name__})")
    return problems


def remaining_estimate(config: dict[str, Any]) -> float:
    ledger = Ledger(out_dir(config) / "ledger.jsonl")
    per_run = (config.get("budget") or {}).get("per_run_usd", {})
    total = 0.0
    for block in schedule(config):
        done = {arm for arm, _ in ledger.done_units(block.block_id)}
        total += sum(float(per_run.get(arm, 0.0)) for arm in block.arms if arm not in done)
    return total


# ---------------------------------------------------------------------------- one unit

def is_control(arm_args: list[str]) -> bool:
    return "--route" in arm_args and arm_args[arm_args.index("--route") + 1] == "control"


def classify(run_dir: Path | None, arm_args: list[str]) -> dict[str, Any]:
    """The unit's result: verdict, grade, and whether it is an outage (never a model outcome)."""
    if run_dir is None:
        return {"outage": "no run folder"}
    results = sorted((run_dir / "results").glob("*/result.json")) if (run_dir / "results").is_dir() else []
    if len(results) != 1:
        return {"outage": f"{len(results)} result files"}
    result = json.loads(results[0].read_text(encoding="utf-8"))
    record = {"verdict": result.get("verdict"), "grade": (result.get("ground_truth_grade") or {}).get("grade"),
              "result_dir": str(results[0].parent)}
    error = result.get("harness_error") or {}
    if result.get("verdict") == "HARNESS_ERROR" and error.get("category") == "PROVIDER_UNAVAILABLE":
        record["outage"] = f"provider unavailable ({error.get('status')})"
    if is_control(arm_args):
        events = sorted(results[0].parent.glob("**/events.jsonl"))
        ids = [json.loads(line).get("payload", {}).get("response_id") for f in events
               for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not any(ids):
            record["outage"] = "Control obtained no generation"
    return record


def run_unit(config: dict[str, Any], block: Block, arm: str, attempt: int, logs: Path) -> dict[str, Any]:
    tree = worktree(config, arm)
    arm_out = out_dir(config) / arm
    arm_out.mkdir(parents=True, exist_ok=True)
    before = {p.name for p in arm_out.iterdir() if p.is_dir()}
    log = logs / f"{block.block_id.replace(':', '_')}-a{attempt}-{arm}.log"
    env = {**os.environ, "PDLT_CATALOGUE_RUNS": str(arm_out), "PYTHONIOENCODING": "utf-8"}
    started = time.time()
    with log.open("w", encoding="utf-8") as handle:
        proc = subprocess.Popen(unit_command(config, arm, block.item_id), cwd=tree, env=env, stdout=handle,
                                stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        try:
            exit_code = proc.wait(timeout=UNIT_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
            else:
                proc.kill()
            exit_code = proc.wait()
    new = sorted(p for p in arm_out.iterdir() if p.is_dir() and p.name not in before)
    record = classify(new[-1] if len(new) == 1 else None, config["arms"][arm]["args"])
    return {"block_id": block.block_id, "attempt": attempt, "arm": arm, "branch": None, "item": block.item_id,
            "rep": block.rep, "status": "done", "run_dir": str(new[-1]) if len(new) == 1 else None,
            "runner_exit": exit_code, "wall_s": round(time.time() - started, 1), "log": str(log), **record}


# ---------------------------------------------------------------------------- commands

def cmd_plan(config: dict[str, Any], args: argparse.Namespace) -> int:
    blocks = schedule(config)
    text = schedule_json(blocks)
    est = estimate(config, blocks)
    print(json.dumps({"study": config["study"], "blocks": len(blocks), "schedule_sha256": sha256(text), **est},
                     indent=1))
    if args.write_schedule:
        schedule_path(config).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {schedule_path(config)}")
    return 0


def cmd_preflight(config: dict[str, Any], args: argparse.Namespace) -> int:
    problems = preflight(config)
    for problem in problems:
        print(f"PREFLIGHT: {problem}")
    print("preflight: ready" if not problems else f"preflight: {len(problems)} problem(s)")
    return 0 if not problems else 1


def _manifest(config: dict[str, Any], blocks: list[Block], key: dict[str, Any]) -> dict[str, Any]:
    return {"study": config["study"], "config": config["_path"],
            "config_sha256": sha256(Path(config["_path"]).read_bytes()),
            "schedule_sha256": sha256(schedule_json(blocks)), "driver_commit": git(ROOT, "rev-parse", "HEAD"),
            "arms": {arm: {"worktree": str(worktree(config, arm)), "commit": git(worktree(config, arm), "rev-parse",
                                                                                   "HEAD"),
                           "args": [*config.get("shared_args", []), *config["arms"][arm]["args"]]}
                     for arm in sorted(config["arms"])},
            "python": sys.version, "platform": platform.platform(),
            "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "key_at_start": key}


def unit_identity(row: dict[str, Any], frozen: dict[str, Any]) -> dict[str, Any] | None:
    """Recorded source/settings only: historical analysis never queries the old worktree."""
    if not row.get("result_dir"):
        if not row.get("outage"):
            raise ValueError("accepted unit has no result or recorded outage")
        return None  # the report retains missing-result/outage diagnostics
    result_dir = Path(row["result_dir"])
    run_dir = Path(row["run_dir"]) if row.get("run_dir") else result_dir.parent.parent
    meta = json.loads((run_dir / "RUN_META.json").read_text(encoding="utf-8"))
    result = json.loads((result_dir / "result.json").read_text(encoding="utf-8"))
    if not isinstance(meta, dict) or not isinstance(result, dict) or not isinstance(meta.get("code"), dict):
        raise ValueError("unit has malformed source/result metadata")
    code = meta["code"]
    if (code.get("commit") != frozen["arms"][row["arm"]]["commit"] or code.get("dirty") is not False
            or meta.get("repeat") != 1 or meta.get("prompt_id_filter") != row["item"]
            or result.get("id") != row["item"]):
        raise ValueError(f"{row['block_id']} {row['arm']}: recorded unit identity differs from the frozen study")
    if not isinstance(meta.get("model"), str) or not isinstance(meta.get("run_settings"), dict):
        raise ValueError("unit has no recorded model or execution settings")
    return {key: meta.get(key) for key in ("model", "route", "reasoning_effort", "reasoning_by_operation",
            "reasoning_effective", "run_settings", "sandbox", "timeout_per_prompt", "harness_memory_mb")}


def validate_study(config: dict[str, Any], *, executing: bool = False) -> tuple[dict[str, Any], dict[str, dict]]:
    """Refuse identity drift before reusing measurements; execution also checks the live checkouts."""
    path = out_dir(config) / "STUDY_MANIFEST.json"
    try:
        frozen = json.loads(path.read_text(encoding="utf-8"))
        blocks = schedule(config)
        if (frozen["study"] != config["study"]
                or frozen["config_sha256"] != sha256(Path(config["_path"]).read_bytes())
                or frozen["schedule_sha256"] != sha256(schedule_json(blocks))
                or set(frozen["arms"]) != set(config["arms"])):
            raise ValueError("configuration, schedule or arm set changed")
        snapshot = schedule_path(config)
        if snapshot.is_file() and sha256(snapshot.read_text(encoding="utf-8")) != frozen["schedule_sha256"]:
            raise ValueError("preserved schedule differs from the frozen identity")
        if executing and not isinstance((frozen.get("key_at_start") or {}).get("usage"), (int, float)):
            raise ValueError("manifest has no starting key usage")
        for arm, spec in config["arms"].items():
            recorded = frozen["arms"][arm]
            if recorded["args"] != [*config.get("shared_args", []), *spec["args"]]:
                raise ValueError(f"{arm}: arguments changed")
            if not isinstance(recorded["commit"], str) or not recorded["commit"]:
                raise ValueError(f"{arm}: missing frozen source commit")
            if executing and recorded["commit"] != git(worktree(config, arm), "rev-parse", "HEAD"):
                raise ValueError(f"{arm}: source commit changed")
        if executing and frozen["driver_commit"] != git(ROOT, "rev-parse", "HEAD"):
            raise ValueError("study driver commit changed")
        expected = {(b.block_id, arm): (b.item_id, b.rep) for b in blocks for arm in b.arms}
        seen, settings = set(), {}
        for row in Ledger(out_dir(config) / "ledger.jsonl").results():
            key = row["block_id"], row["arm"]
            if (key in seen or key not in expected or row.get("branch") is not None
                    or (row["item"], row["rep"]) != expected[key]):
                raise ValueError(f"duplicate or unscheduled accepted unit {key}")
            seen.add(key)
            identity = unit_identity(row, frozen)
            if identity is not None:
                if row["arm"] in settings and settings[row["arm"]] != identity:
                    raise ValueError(f"{row['arm']}: recorded execution settings changed between accepted units")
                settings[row["arm"]] = identity
        return frozen, settings
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"study identity invalid ({path}): {exc}; preserve these records and use a fresh output "
                         "directory for a changed study") from exc


def cmd_run(config: dict[str, Any], args: argparse.Namespace) -> int:
    out = out_dir(config)
    manifest_path = out / "STUDY_MANIFEST.json"
    frozen, identities = None, {}
    if manifest_path.exists() or (out / "ledger.jsonl").exists():
        try:
            frozen, identities = validate_study(config, executing=True)
        except ValueError as exc:
            print(f"IDENTITY: {exc}", flush=True)
            return 1
    problems = preflight(config)
    if problems:
        for problem in problems:
            print(f"PREFLIGHT: {problem}", flush=True)
        return 1
    blocks = schedule(config)
    logs = out / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(out / "ledger.jsonl")
    if frozen is None:
        frozen = _manifest(config, blocks, key_state())
        manifest_path.write_text(json.dumps(frozen, indent=1), encoding="utf-8")
    start_usage = frozen["key_at_start"]["usage"]
    budget = config.get("budget") or {}
    per_run = budget.get("per_run_usd", {})
    failed_in_a_row = 0
    done_blocks = 0
    for block in blocks:
        if args.max_blocks is not None and done_blocks >= args.max_blocks:
            break
        if not set(block.arms) - {a for a, _ in ledger.done_units(block.block_id)}:
            continue
        while True:
            state = key_state()
            block_cost = sum(float(per_run.get(a, 0.0)) for a in block.arms)
            spent = state["usage"] - start_usage
            if (state["limit_remaining"] is not None
                    and state["limit_remaining"] < float(budget.get("reserve_usd", 0.25)) + block_cost):
                print(f"STOP: the key has ${state['limit_remaining']:.2f} left (block {block.block_id})", flush=True)
                return 3
            if spent + block_cost > float(budget.get("cap_usd", float("inf"))):
                print(f"STOP: the study has spent ${spent:.2f} of its ${budget['cap_usd']} cap", flush=True)
                return 3
            attempt = ledger.attempt(block.block_id)
            done = {a for a, _ in ledger.done_units(block.block_id)}
            outage = None
            for arm in block.arms:
                if arm in done:
                    continue
                row = run_unit(config, block, arm, attempt, logs)
                try:
                    identity = unit_identity(row, frozen)
                    if identity is not None:
                        if arm in identities and identities[arm] != identity:
                            raise ValueError(f"{arm}: new unit has different execution settings")
                        identities[arm] = identity
                except (ValueError, OSError, KeyError, TypeError) as exc:
                    ledger.append({**row, "status": "void_unit", "identity_error": str(exc)})
                    print(f"IDENTITY: {exc}", flush=True)
                    return 1
                last = attempt > MAX_BLOCK_RERUNS
                if row.get("outage") and not last:
                    outage = f"{arm}: {row['outage']}"
                    ledger.append({**row, "status": "void_unit"})
                    break
                ledger.append({**row, "kept_after_reruns": bool(row.get("outage")) and last})
                print(f"{block.block_id} {arm} a{attempt}: {row.get('verdict')} {row.get('grade')} "
                      f"{row['wall_s']}s" + (f" OUTAGE {row['outage']}" if row.get("outage") else ""), flush=True)
            if outage is None:
                failed_in_a_row = 0 if not any(r.get("kept_after_reruns") for r in ledger.results()
                                               if r["block_id"] == block.block_id) else failed_in_a_row + 1
                break
            ledger.void_block(block.block_id, outage)
            print(f"{block.block_id}: voided ({outage}); re-run after {OUTAGE_BACKOFF_S}s", flush=True)
            time.sleep(OUTAGE_BACKOFF_S)
        done_blocks += 1
        if failed_in_a_row >= MAX_FAILED_BLOCKS_IN_A_ROW:
            print(f"STOP: {failed_in_a_row} blocks in a row still failing after re-runs (a sustained outage)",
                  flush=True)
            return 3
    pending = [b for b in blocks if set(b.arms) - {a for a, _ in ledger.done_units(b.block_id)}]
    print(f"finished: {len(blocks) - len(pending)} of {len(blocks)} blocks", flush=True)
    return 0 if not pending else 3


def cmd_status(config: dict[str, Any], args: argparse.Namespace) -> int:
    blocks = schedule(config)
    ledger = Ledger(out_dir(config) / "ledger.jsonl")
    rows = ledger.results()
    by_arm: dict[str, int] = {}
    for r in rows:
        by_arm[r["arm"]] = by_arm.get(r["arm"], 0) + 1
    want = estimate(config, blocks)["runs"]
    voids = sum(1 for r in ledger.rows() if r["status"] == "void")
    print(json.dumps({"done": by_arm, "scheduled": want, "voided_blocks": voids,
                      "kept_after_reruns": sum(1 for r in rows if r.get("kept_after_reruns"))}, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "preflight", "run", "status"):
        p = sub.add_parser(name)
        p.add_argument("config", type=Path)
        if name == "plan":
            p.add_argument("--write-schedule", action="store_true")
        if name == "run":
            p.add_argument("--max-blocks", type=int, default=None)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    return {"plan": cmd_plan, "preflight": cmd_preflight, "run": cmd_run, "status": cmd_status}[args.command](
        config, args)


if __name__ == "__main__":
    sys.exit(main())
