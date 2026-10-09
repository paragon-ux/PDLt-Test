"""Fixed-entity experiment (ENTITY_VNEXT_PLAN.md section 5.2): one frozen BOOTSTRAP reply per prompt,
three EXECUTE input conditions, the catalogue's own runner and graders.

    py -3.11 experiments/l100_vnext/fixed_entity.py freeze OUT_DIR
        the frozen replies: for each prompt, L99's (the original's) first repeat, first BOOTSTRAP reply
        (the rule fixed before any result), with that run's System 1 decisions for the dry run.
    py -3.11 experiments/l100_vnext/fixed_entity.py dryrun OUT_DIR
        offline, no network: each prompt x arm through run_catalogue.run_single_prompt and frozen_cli.py,
        capturing the EXECUTE body. Pass: B's body equals the one L99 sent in that run, byte for byte;
        A's and C's differ from B's only in TASK_ENTITIES (A: []; C: condition and relation null).
    py -3.11 experiments/l100_vnext/fixed_entity.py run OUT_DIR [--repeats 20] [--cap 0.95]
        live (spends money): blocks of 9 runs (3 arms x 3 prompts) in a seeded random order; resumable;
        stops between blocks once the key has been charged CAP dollars by this experiment.
    py -3.11 experiments/l100_vnext/fixed_entity.py report OUT_DIR
        per prompt and arm: PASS of decided runs, verdicts, failure reasons; and, from each run's
        provider-requests/, that its first EXECUTE body differs from B's frozen one only as its arm says.

Arms: A no entity block (--no-task-entities: TASK_ENTITIES is present and empty), B the full block,
C the block without the model-written meanings (each entity's relation removed from the frozen reply,
so the host forwards condition and relation as null).
"""
from __future__ import annotations

import collections
import json
import os
import random
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE)]

L99 = ROOT / "catalogue-runs" / "run-20261009-042907-unconfirmed-tier-d1"
PROMPTS = ("01-01", "04-06", "16-06")
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
    # the serialization itself: re-serialize B's document with the arm's entities and compare bytes
    rebuilt = {**ref, "operation_inputs": {**ref_inputs, "TASK_ENTITIES": expected}}
    if json.dumps(rebuilt, ensure_ascii=False, separators=(",", ":")) + ref_tail != body["input"]:
        return "input bytes"
    return None


def freeze(out: Path) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    manifest, frozen = _manifest(), {}
    for pid in PROMPTS:
        entry = manifest[pid]
        result_dir = next((L99 / "results").glob(f"{pid}_*_r1"))
        turn = next(result_dir.glob("session/W-*/turns/turn_001"))
        reply = next(turn.glob("stages/10_prompt/output/0001-bootstrap_analysis/model-response.txt")).read_text(encoding="utf-8")
        events = [json.loads(x) for x in (turn / "events/events.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        frozen[entry["file"]] = {
            "id": pid, "source": str(result_dir.relative_to(ROOT)), "reply": reply,
            "sys1": {k: next((e["payload"] for e in events if e["kind"] == k), None) for k in SYS1_EVENTS},
            "recorded_execute": _execute_bodies(result_dir)[0],
        }
    path = out / "frozen-replies.json"
    path.write_text(json.dumps(frozen, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"frozen {len(frozen)} replies (L99 r1, first BOOTSTRAP reply) -> {path}")
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


def _run_one(rc, entry, run_dir: Path, arm: str, repeat: int | None):
    os.environ["PDLT_FROZEN_ARM"] = arm
    return rc.run_single_prompt(entry, run_dir, MODEL, EFFORT, TIMEOUT, repeat_index=repeat,
                                run_settings={**SETTINGS, "task_entities": arm != "A"})


def dryrun(out: Path) -> int:
    frozen_path = freeze(out)
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    os.environ["PDLT_FROZEN_REPLIES"] = str(frozen_path)
    rc, manifest, ok = _runner(), _manifest(), True
    for file, f in frozen.items():
        bodies = {}
        for arm in ARMS:
            capture = out / f"dryrun-{f['id']}-{arm}.jsonl"
            capture.unlink(missing_ok=True)
            os.environ["PDLT_FROZEN_DRYRUN"] = str(capture)
            _run_one(rc, manifest[f["id"]], out / f"dryrun-{arm}", arm, None)
            sent = [json.loads(x) for x in capture.read_text(encoding="utf-8").splitlines()] if capture.exists() else []
            bodies[arm] = next((b for b in sent if '"operation":"EXECUTE_UNCONFIRMED"' in b["input"]), None)
        os.environ.pop("PDLT_FROZEN_DRYRUN", None)
        same_b = bodies["B"] == f["recorded_execute"]
        others = {arm: (_only_entities_differ(bodies[arm], bodies["B"], arm) if bodies[arm] and bodies["B"] else "no body")
                  for arm in ("A", "C")}
        print(f"{f['id']}: B's EXECUTE body == L99 r1's recorded body: {same_b}; A: {others['A'] or 'only entities ([])'}; "
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


def run(out: Path, repeats: int, cap: float) -> int:
    frozen_path = out / "frozen-replies.json"
    if not frozen_path.exists():
        freeze(out)
    os.environ["PDLT_FROZEN_REPLIES"] = str(frozen_path)
    os.environ.pop("PDLT_FROZEN_DRYRUN", None)
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    rc, manifest = _runner(), _manifest()
    log_path = out / "live-log.json"
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else {
        "seed": SEED, "repeats": repeats, "cap_usd": cap, "key_before": _key(), "blocks": []}
    rng = random.Random(SEED)
    plan = []
    for block in range(1, repeats + 1):
        pairs = [(arm, f["id"]) for arm in ARMS for f in frozen.values()]
        rng.shuffle(pairs)
        plan.append((block, pairs))
    for block, pairs in plan:
        spent = _key()["usage"] - log["key_before"]["usage"]
        if spent >= cap:
            print(f"stopped before block {block}: ${spent:.3f} spent, cap ${cap}")
            log["stopped"] = {"before_block": block, "spent": round(spent, 4)}
            break
        for arm, pid in pairs:
            result_dir = next(iter((out / f"arm-{arm}" / "results").glob(f"{pid}_*_r{block}")), None) \
                if (out / f"arm-{arm}" / "results").exists() else None
            if result_dir is not None and (result_dir / "result.json").exists():
                continue
            result = _run_one(rc, manifest[pid], out / f"arm-{arm}", arm, block)
            grade = (result.get("ground_truth_grade") or {}).get("grade")
            print(f"block {block} {arm} {pid}: {grade} {result['verdict']}", flush=True)
        log["blocks"].append({"block": block, "order": pairs, "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
        log_path.write_text(json.dumps(log, indent=1), encoding="utf-8")
    time.sleep(20)  # the key's usage counter settles after the last call
    log["key_after"] = _key()
    log["cost_usd"] = round(log["key_after"]["usage"] - log["key_before"]["usage"], 4)
    log_path.write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(f"cost ${log['cost_usd']}, remaining ${log['key_after']['remaining']:.2f}")
    return 0


def report(out: Path) -> None:
    frozen = json.loads((out / "frozen-replies.json").read_text(encoding="utf-8"))
    by_id = {f["id"]: f for f in frozen.values()}
    rows = collections.defaultdict(list)
    for arm in ARMS:
        for d in sorted((out / f"arm-{arm}" / "results").glob("*")):
            r = json.loads((d / "result.json").read_text(encoding="utf-8"))
            bodies = _execute_bodies(d)
            check = (_only_entities_differ(bodies[0], by_id[r["id"]]["recorded_execute"], arm) if bodies else "no EXECUTE")
            rows[(r["id"], arm)].append({"grade": (r.get("ground_truth_grade") or {}).get("grade"),
                                         "verdict": r["verdict"], "reason": (r.get("ground_truth_grade") or {}).get("reason"),
                                         "input_check": check})
    summary = {}
    for pid in PROMPTS:
        print(f"\n{pid}")
        for arm in ARMS:
            rs = rows[(pid, arm)]
            c = collections.Counter(x["grade"] for x in rs)
            decided = c["PASS"] + c["FAIL"]
            mismatched = [x["input_check"] for x in rs if x["input_check"]]
            summary[f"{pid}:{arm}"] = {"runs": len(rs), "pass": c["PASS"], "decided": decided, "grades": dict(c),
                                       "verdicts": dict(collections.Counter(x["verdict"] for x in rs)),
                                       "input_mismatch": mismatched}
            print(f"  {arm}: PASS {c['PASS']}/{decided} decided ({len(rs)} runs; {dict(c)}); "
                  f"verdicts {dict(collections.Counter(x['verdict'] for x in rs))}; "
                  f"EXECUTE input not as the arm says: {mismatched or 'none'}")
            for reason, n in collections.Counter(str(x["reason"])[:90] for x in rs if x["grade"] != "PASS").most_common(3):
                print(f"      {n}x {reason}")
    (out / "report.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    command, target = sys.argv[1], Path(sys.argv[2])
    if command == "freeze":
        freeze(target)
    elif command == "dryrun":
        raise SystemExit(dryrun(target))
    elif command == "run":
        args = sys.argv[3:]
        repeats = int(args[args.index("--repeats") + 1]) if "--repeats" in args else 20
        cap = float(args[args.index("--cap") + 1]) if "--cap" in args else 0.95
        raise SystemExit(run(target, repeats, cap))
    elif command == "report":
        report(target)
