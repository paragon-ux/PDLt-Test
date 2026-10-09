#!/usr/bin/env python3
"""Judged grading for the PDL pilot (ledger L97, PLAN.md section 3).

    py -3.11 experiments/pdl_format/judge_pilot.py --price --judges NAME=MODEL[,NAME=MODEL]
    py -3.11 experiments/pdl_format/judge_pilot.py --run   --judges NAME=MODEL[,NAME=MODEL]

What is judged, one packet each:
- the fidelity of every prompt artifact and every plan artifact (18 sessions), against its task's
  full criterion list plus one criterion for invented requirements;
- every Task 2 and Task 3 deliverable (the 3 independent executions and the 2 replays per arm),
  against the task's criteria, with the golden facts as the judges' reference.

Packets carry an opaque id, never the arm, repeat or path (the key is written separately); the
format of an artifact still shows its arm, which PLAN.md states. ``--price`` sends nothing to a
judge: it sizes the packets and prices them from OpenRouter's public model list. ``--run`` is the
paid step and needs the user's approval first. Mechanical checks (Task 2 YAML, Task 3 timeline)
are recorded beside the judges' marks.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for entry in (ROOT, ROOT / "src"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from experiments import judge  # noqa: E402
from experiments.pdl_format.run_pilot import OUT, task_prompt  # noqa: E402

SESSIONS = OUT / "sessions"
TASK_IDS = {"T1": "T1_USAGE_RECONCILIATION", "T2": "T2_QUEUE_CUTOVER", "T3": "T3_API_INCIDENT"}
GOLDEN_KEYS = {"T2": "task_2_queue_cutover", "T3": "task_3_api_incident"}
OUTPUT_ALLOWANCE = 2500  # reply tokens a judge call is priced at, reasoning included

FIDELITY_TASK = {
    "prompt": ("An interpretation of the request, written before any work was done: it states what is to be "
               "produced, not the product. For each criterion, mark met if the interpretation states or "
               "unambiguously requires it, in any wording or order; mark not_met if it omits, weakens, distorts or "
               "contradicts it. Do not judge whether the task was carried out."),
    "plan": ("A response plan for the request, written before any work was done: it describes how the deliverable "
             "will be produced, at a high level. For each criterion, mark met if the plan covers it explicitly or "
             "through a broader step, and nothing in the plan contradicts it; mark not_met if the plan omits a step "
             "the criterion needs, contradicts it, or would produce something the criterion forbids. Do not judge "
             "whether the task was carried out."),
}
INVENTED = judge.Criterion("X-INVENTED", "The artifact adds no requirement, constraint or deliverable that the request "
                                         "does not ask for.")
DELIVERABLE_TASK = ("The deliverable produced for the task above. Judge each criterion against the task's own "
                    "requirements; the reference lists facts taken from the task's evidence, for the judge only.")


def criteria(task: str) -> list[judge.Criterion]:
    rows = list(csv.DictReader((HERE / "scoring" / "acceptance-criteria.csv").read_text(encoding="utf-8").splitlines()))
    return [judge.Criterion(r["criterion_id"], r["criterion"]) for r in rows if r["task_id"] == TASK_IDS[task]]


def golden(task: str) -> str:
    data = json.loads((HERE / "scoring" / "golden-expectations.json").read_text(encoding="utf-8"))
    return json.dumps(data[GOLDEN_KEYS[task]], indent=1)


def _artifact(trunk: Path, stage: str) -> str | None:
    files = sorted(trunk.rglob(f"stages/{stage}/output/current.md"), key=lambda p: p.stat().st_mtime)
    return files[-1].read_text(encoding="utf-8") if files else None


def opaque(path: Path) -> str:
    return hashlib.sha256(path.relative_to(ROOT).as_posix().encode()).hexdigest()[:10]


def items() -> list[dict]:
    """Every judged packet: (opaque id, kind, task, rubric, text) and the key back to the session."""
    import graders

    out = []
    for session in sorted(p for p in SESSIONS.iterdir() if p.is_dir()):
        task, arm, repeat = session.name.split("-")
        trunk = session / "trunk"
        for kind, stage in (("prompt", "10_prompt"), ("plan", "30_plan")):
            text = _artifact(trunk, stage)
            if text is not None:
                rubric = judge.Rubric(f"{task}-{kind}", FIDELITY_TASK[kind], (*criteria(task), INVENTED))
                out.append({"id": opaque(trunk / stage), "kind": kind, "task": task, "rubric": rubric, "text": text,
                            "key": {"session": session.name, "arm": arm, "repeat": repeat, "artifact": kind}})
        if task in GOLDEN_KEYS:
            for execution in sorted(session.glob("exec*")):
                text = graders.find_deliverable(execution)
                if text is None:
                    continue
                rubric = judge.Rubric(f"{task}-deliverable", DELIVERABLE_TASK, tuple(criteria(task)), golden(task))
                out.append({"id": opaque(execution), "kind": "deliverable", "task": task, "rubric": rubric,
                            "text": text, "mechanical": mechanical(task, text),
                            "key": {"session": session.name, "arm": arm, "repeat": repeat,
                                    "execution": execution.name}})
    return out


def _fenced(text: str, languages: tuple[str, ...]) -> list[str]:
    pattern = r"^```[ \t]*(?:" + "|".join(languages) + r")[ \t]*\n(.*?)^```"
    return re.findall(pattern, text or "", re.S | re.M | re.I)


def mechanical(task: str, text: str) -> dict:
    """Checks a machine can make, recorded beside the judges' marks (never instead of them)."""
    if task == "T2":
        import yaml

        blocks = _fenced(text, ("yaml", "yml"))
        parsed = []
        for block in blocks:
            try:
                parsed.append(yaml.safe_load(block))
            except yaml.YAMLError:
                parsed.append(None)
        return {"yaml_blocks": len(blocks), "yaml_parses": bool(parsed) and all(p is not None for p in parsed),
                "states_225_minutes": bool(re.search(r"\b225\s*(?:min|minutes)\b", text, re.I))}
    blocks = [b for b in _fenced(text, ("csv", "")) if "timestamp_utc" in b.splitlines()[0]] if text else []
    if not blocks:
        return {"timeline_csv": False}
    rows = list(csv.DictReader(blocks[0].splitlines()))
    stamps = []
    for row in rows:
        try:
            stamps.append(datetime.fromisoformat((row.get("timestamp_utc") or "").replace("Z", "+00:00")))
        except ValueError:
            stamps.append(None)
    valid = [s for s in stamps if s is not None and s.utcoffset() is not None and s.utcoffset().total_seconds() == 0]
    required = {"14:02", "14:03", "14:05", "14:08", "14:11", "14:14", "14:16"}
    present = {s.strftime("%H:%M") for s in valid}
    return {"timeline_csv": True, "header_exact": blocks[0].splitlines()[0].strip() ==
            "timestamp_utc,event,source,evidence_status", "rows": len(rows), "all_utc": len(valid) == len(stamps),
            "sorted": valid == sorted(valid), "required_times_present": sorted(required - present) == [],
            "missing_times": sorted(required - present)}


def parse_judges(spec: str) -> list[judge.JudgeSpec]:
    out = []
    for part in spec.split(","):
        name, model = part.split("=", 1)
        out.append(judge.JudgeSpec(name.strip(), model.strip()))
    return out


def price(packets: list[dict], judges: list[judge.JudgeSpec]) -> dict:
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as response:
        listing = {m["id"]: m for m in json.load(response)["data"]}
    prompts = [judge.judge_prompt(p["rubric"], task_prompt(p["task"]), p["text"]) for p in packets]
    input_tokens = sum(len(p) for p in prompts) / 4  # about four characters a token
    out = {"packets": len(packets), "input_tokens_per_judge": round(input_tokens),
           "output_tokens_per_judge": OUTPUT_ALLOWANCE * len(packets), "judges": {}}
    for spec in judges:
        model = listing.get(spec.model)
        if model is None:
            out["judges"][spec.name] = {"model": spec.model, "error": "not in OpenRouter's model list"}
            continue
        prompt_price, completion_price = float(model["pricing"]["prompt"]), float(model["pricing"]["completion"])
        cost = input_tokens * prompt_price + OUTPUT_ALLOWANCE * len(packets) * completion_price
        out["judges"][spec.name] = {"model": spec.model, "usd_per_m_in": prompt_price * 1e6,
                                    "usd_per_m_out": completion_price * 1e6, "estimate_usd": round(cost, 2)}
    out["total_estimate_usd"] = round(sum(j.get("estimate_usd", 0) for j in out["judges"].values()), 2)
    return out


def run(packets: list[dict], judges: list[judge.JudgeSpec]) -> list[dict]:
    send = judge.openrouter_sender(ROOT)
    results = []
    for packet in packets:
        verdicts = judge.judge(packet["rubric"], task_prompt(packet["task"]), packet["text"], judges, send)
        marks = {}
        for criterion in packet["rubric"].criteria:
            seen = {name: v.get("marks", {}).get(criterion.id) for name, v in verdicts.items()}
            values = set(seen.values())
            marks[criterion.id] = values.pop() if len(values) == 1 and None not in values else {"disagree": seen}
        results.append({"id": packet["id"], "kind": packet["kind"], "task": packet["task"], "marks": marks,
                        "mechanical": packet.get("mechanical"),
                        "notes": {name: (v.get("reply") or v.get("error") or "")[-600:] for name, v in verdicts.items()}})
        print(f"{packet['id']} {packet['kind']} {packet['task']}: "
              f"{sum(1 for m in marks.values() if m == judge.MET)}/{len(marks)} met, "
              f"{sum(1 for m in marks.values() if isinstance(m, dict))} disagreements", flush=True)
    return results


def export(packets: list[dict], out_dir: Path, batches: int) -> None:
    """Manual mode: each packet's judge prompt (the API path's exact text) as ``<id>.txt``, in shuffled batches."""
    import random

    from experiments.grading import strip_for_adjudication

    out_dir.mkdir(parents=True, exist_ok=True)
    for packet in packets:
        text = judge.judge_prompt(packet["rubric"], task_prompt(packet["task"]), strip_for_adjudication(packet["text"]))
        (out_dir / f"{packet['id']}.txt").write_text(text, encoding="utf-8")
    ids = [p["id"] for p in packets]
    random.Random(97).shuffle(ids)  # each batch mixes tasks, kinds and arms
    (out_dir / "batches.json").write_text(json.dumps([ids[n::batches] for n in range(batches)], indent=1),
                                          encoding="utf-8")


def import_replies(packets: list[dict], replies: Path, name: str, model: str) -> list[dict]:
    """Manual mode: marks from ``<id>.reply.txt``, read by the API path's parser; a missing reply is recorded."""
    results = []
    for packet in packets:
        path = replies / f"{packet['id']}.reply.txt"
        reply = path.read_text(encoding="utf-8") if path.is_file() else None
        marks = judge.parse_marks(reply, packet["rubric"]) if reply is not None else {}
        results.append({"id": packet["id"], "kind": packet["kind"], "task": packet["task"], "marks": marks,
                        "mechanical": packet.get("mechanical"), "notes": {name: (reply or "no reply")[-600:]}})
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--price", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--export", type=Path, metavar="DIR", help="manual mode: write the judge prompts")
    mode.add_argument("--import", dest="import_dir", type=Path, metavar="DIR", help="manual mode: read the replies")
    parser.add_argument("--judges", help="NAME=MODEL[,NAME=MODEL]; one judge for --import")
    parser.add_argument("--batches", type=int, default=8)
    args = parser.parse_args(argv)
    if not args.judges and not args.export:
        parser.error("--judges is required")
    judges = parse_judges(args.judges) if args.judges else []
    packets = items()
    (OUT / "judge-key.json").write_text(json.dumps({p["id"]: p["key"] for p in packets}, indent=1), encoding="utf-8")
    if args.export:
        export(packets, args.export, args.batches)
        print(f"{len(packets)} judge prompts in {args.export}")
        return 0
    if args.import_dir:
        results = import_replies(packets, args.import_dir, judges[0].name, judges[0].model)
        (OUT / "judgments.json").write_text(json.dumps({"judges": [j.__dict__ for j in judges[:1]], "results": results},
                                                       indent=1), encoding="utf-8")
        print(f"{sum(1 for r in results if r['marks'])} of {len(results)} packets have replies")
        return 0
    if args.price:
        print(json.dumps(price(packets, judges), indent=1))
        return 0
    results = run(packets, judges)
    (OUT / "judgments.json").write_text(json.dumps({"judges": [j.__dict__ for j in judges], "results": results},
                                                   indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
