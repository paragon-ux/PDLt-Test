"""Fixed-entity experiment (ENTITY_VNEXT_PLAN.md section 5.2): two frozen BOOTSTRAP replies per prompt
(one from a passing run, one from a failing run), three EXECUTE input conditions, the catalogue's own
runner and graders.

    py -3.11 experiments/l100_vnext/fixed_entity.py freeze OUT_DIR
        the frozen replies, chosen by the rule fixed before any result (SELECTION below), with each run's
        System 1 decisions (for the dry run) and the EXECUTE body that run sent (the reference for arm B).
    py -3.11 experiments/l100_vnext/fixed_entity.py dryrun OUT_DIR
        offline, no network: each prompt x reply x arm through run_catalogue.run_single_prompt and
        frozen_cli.py, capturing the EXECUTE body. Pass: B's body equals the one its source run sent, byte
        for byte; A's and C's differ from B's only in TASK_ENTITIES (A: []; C: condition and relation null).
    py -3.11 experiments/l100_vnext/fixed_entity.py run OUT_DIR [--blocks 10] [--cap 0.80]
        live (spends money): blocks of 18 runs (3 prompts x 2 replies x 3 arms) in a seeded random order;
        resumable; stops between blocks once the key has been charged CAP dollars by this experiment.
    py -3.11 experiments/l100_vnext/fixed_entity.py report OUT_DIR
        per prompt: PASS of decided runs per reply and arm, pooled per arm, and B's two replies compared
        (two-sided Fisher exact p); each run's first EXECUTE body checked against its arm.

Arms: A no entity block (--no-task-entities: TASK_ENTITIES is present and empty), B the full block,
C the block without the model-written meanings (each entity's relation removed from the frozen reply, so
the host forwards condition and relation as null; the keys stay, so C changes content and length, not keys).
"""
from __future__ import annotations

import collections
import json
import math
import os
import random
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE)]

SWEEPS = {"orig": ROOT / "catalogue-runs" / "run-20261009-042907-unconfirmed-tier-d1",
          "vnext": ROOT / "catalogue-runs" / "run-20261009-175714-unconfirmed-tier-d1"}
# Rule fixed before any result: per prompt, P = the earliest passing run and F = the earliest failing run,
# the original's sweep (L99) first. 16-06 has no passing original run, so P is the earliest passing vNext run;
# D1 did not fire in it, so the host built its EXECUTE input as the original would (checked in the dry run).
SELECTION = {"01-01": {"P": ("orig", 2), "F": ("orig", 1)},
             "04-06": {"P": ("orig", 1), "F": ("orig", 3)},
             "16-06": {"P": ("vnext", 1), "F": ("orig", 2)}}
PROMPTS = tuple(SELECTION)
REPLIES = ("P", "F")
ARMS = ("A", "B", "C")
SEED = 20261009
MODEL, EFFORT, TIMEOUT = "openai/gpt-oss-120b", "low", 300
SETTINGS = {"max_output_tokens": None, "max_repairs": None, "providers": "Cerebras", "draft_execute": False,
            "representation": "pdl", "tier_d1": True, "sandbox": None, "route": "unconfirmed",
            "theme": None, "user_color": None, "assistant_color": None}
SYS1_EVENTS = ("ACTIVATION_ROUTED", "PROBLEM_CLASS_CLASSIFIED", "EXECUTION_PROFILE_ROUTED")


def _manifest() -> dict:
    lines = (ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl").read_text(encoding="utf-8-sig").splitlines()
    return {e["id"]: e for e in (json.loads(x) for x in lines if x.strip())}


def _split(text: str):
    doc, end = json.JSONDecoder().raw_decode(text)
    return doc, text[end:]


def _execute_bodies(result_dir: Path) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(result_dir.glob("session/*/provider-requests/*-EXECUTE_UNCONFIRMED-*-a1.json"))]


def _only_entities_differ(body: dict, reference: dict, arm: str) -> str | None:
    """None when body differs from reference (arm B's body) only as the arm says; else what differs."""
    for key in set(body) | set(reference):
        if key != "input" and body.get(key) != reference.get(key):
            return f"body.{key}"
    doc, tail = _split(body["input"])
    ref, ref_tail = _split(reference["input"])
    if tail != ref_tail:
        return "input tail"
    for key in set(doc) | set(ref):
        if key != "operation_inputs" and doc.get(key) != ref.get(key):
            return f"doc.{key}"
    inputs, ref_inputs = doc["operation_inputs"], ref["operation_inputs"]
    for key in set(inputs) | set(ref_inputs):
        if key != "TASK_ENTITIES" and inputs.get(key) != ref_inputs.get(key):
            return f"operation_inputs.{key}"
    entities, ref_entities = inputs.get("TASK_ENTITIES"), ref_inputs.get("TASK_ENTITIES")
    expected = {"A": [], "B": ref_entities,
                "C": [{**e, "condition": None, "relation": None} for e in ref_entities or []]}[arm]
    if entities != expected:
        return "TASK_ENTITIES not as the arm says"
    rebuilt = {**ref, "operation_inputs": {**ref_inputs, "TASK_ENTITIES": expected}}
    if json.dumps(rebuilt, ensure_ascii=False, separators=(",", ":")) + ref_tail != body["input"]:
        return "input bytes"
    return None


def freeze(out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    manifest, frozen = _manifest(), {}
    for pid, picks in SELECTION.items():
        entry = manifest[pid]
        frozen[entry["file"]] = {}
        for label, (sweep, repeat) in picks.items():
            result_dir = next((SWEEPS[sweep] / "results").glob(f"{pid}_*_r{repeat}"))
            turn = next(result_dir.glob("session/W-*/turns/turn_001"))
            reply = next(turn.glob("stages/10_prompt/output/0001-bootstrap_analysis/model-response.txt")).read_text(encoding="utf-8")
            events = [json.loads(x) for x in (turn / "events/events.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
            grade = (json.loads((result_dir / "result.json").read_text(encoding="utf-8")).get("ground_truth_grade") or {}).get("grade")
            assert grade == {"P": "PASS", "F": "FAIL"}[label], (pid, label, grade)
            assert not any(e["kind"] == "TASK_ENTITY_UNANCHORED" for e in events), (pid, label, "D1 fired")
            frozen[entry["file"]][label] = {
                "id": pid, "source": str(result_dir.relative_to(ROOT)), "grade": grade, "reply": reply,
                "sys1": {k: next((e["payload"] for e in events if e["kind"] == k), None) for k in SYS1_EVENTS},
                "recorded_execute": _execute_bodies(result_dir)[0],
            }
    path = out / "frozen-replies.json"
    path.write_text(json.dumps(frozen, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"frozen {sum(len(v) for v in frozen.values())} replies ({len(frozen)} prompts) -> {path}")
    return path


def _runner():
    import run_catalogue

    original = run_catalogue.build_harness_command

    def command(*args, **kwargs):
        cmd = original(*args, **kwargs)
        assert cmd[1:3] == ["-m", "pdl_taskmaster.host.cli"], cmd[:3]
        return [cmd[0], str(HERE / "frozen_cli.py"), *cmd[3:]]

    run_catalogue.build_harness_command = command
    return run_catalogue


def _run_one(rc, entry, run_dir: Path, reply: str, arm: str, block: int | None):
    os.environ["PDLT_FROZEN_REPLY"], os.environ["PDLT_FROZEN_ARM"] = reply, arm
    return rc.run_single_prompt(entry, run_dir, MODEL, EFFORT, TIMEOUT, repeat_index=block,
                                run_settings={**SETTINGS, "task_entities": arm != "A"})


def dryrun(out: Path) -> int:
    frozen_path = freeze(out)
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    os.environ["PDLT_FROZEN_REPLIES"] = str(frozen_path)
    rc, manifest, ok = _runner(), _manifest(), True
    for file, replies in frozen.items():
        for label, f in replies.items():
            bodies = {}
            for arm in ARMS:
                capture = out / f"dryrun-{f['id']}-{label}-{arm}.jsonl"
                capture.unlink(missing_ok=True)
                os.environ["PDLT_FROZEN_DRYRUN"] = str(capture)
                _run_one(rc, manifest[f["id"]], out / f"dryrun-{label}-{arm}", label, arm, None)
                sent = [json.loads(x) for x in capture.read_text(encoding="utf-8").splitlines()] if capture.exists() else []
                bodies[arm] = next((b for b in sent if '"operation":"EXECUTE_UNCONFIRMED"' in b["input"]), None)
            os.environ.pop("PDLT_FROZEN_DRYRUN", None)
            same_b = bodies["B"] == f["recorded_execute"]
            others = {arm: (_only_entities_differ(bodies[arm], bodies["B"], arm) if bodies[arm] and bodies["B"] else "no body")
                      for arm in ("A", "C")}
            print(f"{f['id']} {label} ({f['source'].split(chr(92))[-1] if chr(92) in f['source'] else f['source']}): "
                  f"B == its run's recorded EXECUTE body: {same_b}; A: {others['A'] or 'only entities ([])'}; "
                  f"C: {others['C'] or 'only entities (meanings null)'}")
            ok = ok and same_b and not any(others.values())
    print("dry run", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def _key() -> dict:
    req = urllib.request.Request("https://openrouter.ai/api/v1/key",
                                 headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
                                          "User-Agent": "pdlt-fixed-entity/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)["data"]
    return {"usage": data["usage"], "remaining": data["limit_remaining"]}


def run(out: Path, blocks: int, cap: float) -> int:
    frozen_path = out / "frozen-replies.json"
    if not frozen_path.exists():
        freeze(out)
    os.environ["PDLT_FROZEN_REPLIES"] = str(frozen_path)
    os.environ.pop("PDLT_FROZEN_DRYRUN", None)
    rc, manifest = _runner(), _manifest()
    log_path = out / "live-log.json"
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else {
        "seed": SEED, "blocks_planned": blocks, "cap_usd": cap, "key_before": _key(), "blocks": []}
    rng = random.Random(SEED)
    plan = []
    for block in range(1, blocks + 1):
        cells = [(pid, label, arm) for pid in PROMPTS for label in REPLIES for arm in ARMS]
        rng.shuffle(cells)
        plan.append((block, cells))
    for block, cells in plan:
        spent = _key()["usage"] - log["key_before"]["usage"]
        if spent >= cap:
            print(f"stopped before block {block}: ${spent:.3f} spent, cap ${cap}")
            log["stopped"] = {"before_block": block, "spent": round(spent, 4)}
            break
        for pid, label, arm in cells:
            results = out / f"{label}-{arm}" / "results"
            done = results.exists() and any((d / "result.json").exists() for d in results.glob(f"{pid}_*_r{block}"))
            if done:
                continue
            result = _run_one(rc, manifest[pid], out / f"{label}-{arm}", label, arm, block)
            grade = (result.get("ground_truth_grade") or {}).get("grade")
            print(f"block {block} {pid} {label} {arm}: {grade} {result['verdict']}", flush=True)
        if not any(b["block"] == block for b in log["blocks"]):
            log["blocks"].append({"block": block, "order": cells, "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
        log_path.write_text(json.dumps(log, indent=1), encoding="utf-8")
    time.sleep(20)  # the key's usage counter settles after the last call
    log["key_after"] = _key()
    log["cost_usd"] = round(log["key_after"]["usage"] - log["key_before"]["usage"], 4)
    log_path.write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(f"cost ${log['cost_usd']}, remaining ${log['key_after']['remaining']:.2f}")
    return 0


def fisher(a: int, n1: int, c: int, n2: int) -> float:
    """Two-sided Fisher exact p for a/n1 against c/n2."""
    total, k = n1 + n2, a + c
    if n1 == 0 or n2 == 0:
        return float("nan")
    p_of = lambda x: math.comb(n1, x) * math.comb(n2, k - x) / math.comb(total, k)
    observed = p_of(a)
    return min(1.0, sum(p_of(x) for x in range(max(0, k - n2), min(k, n1) + 1) if p_of(x) <= observed * (1 + 1e-9)))


def report(out: Path) -> None:
    frozen = json.loads((out / "frozen-replies.json").read_text(encoding="utf-8"))
    ref = {(f["id"], label): f["recorded_execute"] for replies in frozen.values() for label, f in replies.items()}
    cells = {}
    for pid in PROMPTS:
        for label in REPLIES:
            for arm in ARMS:
                rows = []
                for d in sorted((out / f"{label}-{arm}" / "results").glob(f"{pid}_*")):
                    r = json.loads((d / "result.json").read_text(encoding="utf-8"))
                    bodies = _execute_bodies(d)
                    rows.append({"grade": (r.get("ground_truth_grade") or {}).get("grade"), "verdict": r["verdict"],
                                 "reason": str((r.get("ground_truth_grade") or {}).get("reason"))[:90],
                                 "input_check": _only_entities_differ(bodies[0], ref[(pid, label)], arm) if bodies else "no EXECUTE"})
                c = collections.Counter(x["grade"] for x in rows)
                cells[(pid, label, arm)] = {"runs": len(rows), "pass": c["PASS"], "decided": c["PASS"] + c["FAIL"],
                                            "grades": dict(c), "verdicts": dict(collections.Counter(x["verdict"] for x in rows)),
                                            "input_mismatch": [x["input_check"] for x in rows if x["input_check"]],
                                            "fail_reasons": collections.Counter(x["reason"] for x in rows if x["grade"] != "PASS").most_common(3)}
    fmt = lambda x: f"{x['pass']}/{x['decided']}"
    summary = {"cells": {"|".join(k): v for k, v in cells.items()}, "tests": {}}
    for pid in PROMPTS:
        print(f"\n{pid}")
        for label in REPLIES:
            row = "  ".join(f"{arm} {fmt(cells[(pid, label, arm)])}" for arm in ARMS)
            print(f"  reply {label}: {row}")
            for arm in ARMS:
                x = cells[(pid, label, arm)]
                if x["input_mismatch"]:
                    print(f"    {arm}: EXECUTE input not as the arm says: {x['input_mismatch']}")
        pooled = {arm: (sum(cells[(pid, l, arm)]["pass"] for l in REPLIES), sum(cells[(pid, l, arm)]["decided"] for l in REPLIES))
                  for arm in ARMS}
        tests = {"B vs A": (pooled["B"], pooled["A"]), "C vs B": (pooled["C"], pooled["B"]), "C vs A": (pooled["C"], pooled["A"]),
                 "B: reply P vs F": ((cells[(pid, "P", "B")]["pass"], cells[(pid, "P", "B")]["decided"]),
                                     (cells[(pid, "F", "B")]["pass"], cells[(pid, "F", "B")]["decided"]))}
        for name, ((a, n1), (c, n2)) in tests.items():
            p = fisher(a, n1, c, n2)
            summary["tests"][f"{pid} {name}"] = {"left": [a, n1], "right": [c, n2], "p": p}
            print(f"  {name}: {a}/{n1} vs {c}/{n2}, Fisher p = {p:.3f}")
    (out / "report.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=str), encoding="utf-8")


if __name__ == "__main__":
    command, target = sys.argv[1], Path(sys.argv[2])
    args = sys.argv[3:]
    if command == "freeze":
        freeze(target)
    elif command == "dryrun":
        raise SystemExit(dryrun(target))
    elif command == "run":
        blocks = int(args[args.index("--blocks") + 1]) if "--blocks" in args else 10
        cap = float(args[args.index("--cap") + 1]) if "--cap" in args else 0.80
        raise SystemExit(run(target, blocks, cap))
    elif command == "report":
        report(target)
